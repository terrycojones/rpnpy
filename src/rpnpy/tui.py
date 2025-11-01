"""Terminal User Interface for rpnpy calculator using Textual."""

from io import StringIO
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, Static

from rpnpy.calculator import Calculator
from rpnpy.errors import CalculatorError, StackError


class StackDisplay(Static):
    """Widget to display the calculator stack."""

    def __init__(self, calc: Calculator, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.calc = calc

    def update_display(self) -> None:
        """Update the stack display with current stack contents."""
        if not self.calc.stack:
            content = "[dim]Stack is empty[/dim]"
        else:
            lines = []
            for i, item in enumerate(self.calc.stack):
                # Format the item nicely using repr() to show strings with quotes
                # and handle complex objects properly
                if isinstance(item, float):
                    # Format floats without excessive precision
                    formatted = f"{item:.10g}"
                elif isinstance(item, str):
                    # Show strings with quotes
                    formatted = repr(item)
                elif isinstance(item, (list, dict, tuple, set)):
                    # For complex objects, use repr but limit length for display
                    formatted = repr(item)
                    if len(formatted) > 80:
                        formatted = formatted[:77] + "..."
                else:
                    # For everything else, use repr
                    formatted = repr(item)
                lines.append(f"[bold cyan]{i}:[/bold cyan] {formatted}")
            content = "\n".join(lines)
        self.update(content)


class VariablesDisplay(Static):
    """Widget to display calculator variables."""

    def __init__(self, calc: Calculator, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.calc = calc

    def update_display(self) -> None:
        """Update the variables display with current variables."""
        # Only show basic value types - not modules, functions, classes, etc.
        # Just show the data values that users would think of as "variables"
        variables = {}
        for k, v in self.calc._variables.items():
            # Skip internal/system names, inf, and nan
            if k.startswith("_") or k == "self" or k in ("inf", "nan"):
                continue
            # Only include basic value types
            if isinstance(v, (int, float, str, list, dict, tuple, set, bool, type(None))):
                variables[k] = v

        if not variables:
            content = "[dim]No variables defined[/dim]"
        else:
            lines = []
            for name in sorted(variables.keys()):
                value = variables[name]
                # Format the value
                if isinstance(value, float):
                    formatted = f"{value:.10g}"
                elif isinstance(value, str):
                    formatted = repr(value)
                elif isinstance(value, (list, dict, tuple, set)):
                    formatted = repr(value)
                    if len(formatted) > 60:
                        formatted = formatted[:57] + "..."
                else:
                    formatted = repr(value)
                lines.append(f"[bold green]{name}:[/bold green] {formatted}")
            content = "\n".join(lines)
        self.update(content)


class CalculatorButton(Button):
    """A calculator button that can send a command to the calculator."""

    can_focus = False

    def __init__(self, label: str, command: str, variant: str = "default", **kwargs: Any) -> None:
        super().__init__(label, variant=variant, **kwargs)
        self.command = command


class CalculatorTUI(App):
    """A Textual TUI for the RPN calculator."""

    TITLE = "rpnpy TUI"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        width: 100%;
    }

    #left-panel {
        width: 60%;
        height: 100%;
        border: thick $primary;
        padding: 1 2;
        background: $boost;
        overflow-y: auto;
    }

    #right-panel {
        width: 40%;
        height: 100%;
        border: thick $accent;
        padding: 1 2;
        background: $boost;
    }

    #button-grid {
        width: 100%;
        height: auto;
        padding: 1 0;
    }

    .button-row {
        height: auto;
        width: 100%;
        margin: 0 0 0 0;
        padding: 0 0 1 0;
    }

    CalculatorButton {
        width: 1fr;
        margin: 0 1;
        min-width: 8;
        height: 3;
        min-height: 3;
    }

    #stack-container {
        height: 1fr;
        border: solid $accent;
        margin: 0 0 1 0;
        background: $boost;
        padding: 1;
    }

    #variables-container {
        height: 1fr;
        border: solid $accent;
        background: $boost;
        padding: 1;
    }

    #stack-title {
        text-style: bold;
        color: $accent;
        margin: 0 0 1 0;
        text-align: center;
    }

    #variables-title {
        text-style: bold;
        color: $success;
        margin: 0 0 1 0;
        text-align: center;
    }

    #stack-display {
        border: solid $primary-lighten-1;
        padding: 1;
        height: 1fr;
        background: $panel;
        overflow-y: auto;
    }

    #variables-display {
        border: solid $success-lighten-1;
        padding: 1;
        height: 1fr;
        background: $panel;
        overflow-y: auto;
    }


    #title {
        text-style: bold;
        color: $accent;
        margin: 0 0 1 0;
        text-align: center;
    }

    #input-field {
        margin: 0 0 1 0;
        border: solid $success;
    }

    #input-label {
        margin: 0 0 1 0;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "clear_input", "Clear Input"),
    ]

    def __init__(self, calc: Calculator, error_buffer: StringIO, theme: str = "nord") -> None:
        super().__init__()
        self.calc = calc
        self.error_buffer = error_buffer
        self.theme_name = theme

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()

        with Horizontal(id="main-container"):
            # Left panel - Calculator buttons and input
            with Vertical(id="left-panel"):
                yield Label("rpnpy TUI", id="title")
                yield Label("Enter number or command:", id="input-label")
                yield Input(placeholder="Type and press Enter...", id="input-field")
                yield from self._create_button_grid()

            # Right panel - Stack and Variables display
            with Vertical(id="right-panel"):
                # Stack section
                with Vertical(id="stack-container"):
                    yield Label("Stack", id="stack-title")
                    yield StackDisplay(self.calc, id="stack-display")

                # Variables section
                with Vertical(id="variables-container"):
                    yield Label("Variables", id="variables-title")
                    yield VariablesDisplay(self.calc, id="variables-display")

        yield Footer()

    def _create_button_grid(self) -> ComposeResult:
        """Create the calculator button grid."""
        with Container(id="button-grid"):
            # Number buttons (7-9) and division
            with Horizontal(classes="button-row"):
                yield CalculatorButton("7", "7", variant="primary")
                yield CalculatorButton("8", "8", variant="primary")
                yield CalculatorButton("9", "9", variant="primary")
                yield CalculatorButton("÷", "/", variant="warning")

            # Number buttons (4-6) and multiplication
            with Horizontal(classes="button-row"):
                yield CalculatorButton("4", "4", variant="primary")
                yield CalculatorButton("5", "5", variant="primary")
                yield CalculatorButton("6", "6", variant="primary")
                yield CalculatorButton("×", "*", variant="warning")

            # Number buttons (1-3) and subtraction
            with Horizontal(classes="button-row"):
                yield CalculatorButton("1", "1", variant="primary")
                yield CalculatorButton("2", "2", variant="primary")
                yield CalculatorButton("3", "3", variant="primary")
                yield CalculatorButton("-", "-", variant="warning")

            # Number 0, decimal point, and addition
            with Horizontal(classes="button-row"):
                yield CalculatorButton("0", "0", variant="primary")
                yield CalculatorButton(".", ".", variant="primary")
                yield CalculatorButton("Enter", "enter", variant="success")
                yield CalculatorButton("+", "+", variant="warning")

            # Mathematical functions row 1
            with Horizontal(classes="button-row"):
                yield CalculatorButton("√x", "sqrt", variant="default")
                yield CalculatorButton("x²", "2 pow", variant="default")
                yield CalculatorButton("xʸ", "pow", variant="default")
                yield CalculatorButton("1/x", "1 swap /", variant="default")

            # Mathematical functions row 2
            with Horizontal(classes="button-row"):
                yield CalculatorButton("log", "log10", variant="default")
                yield CalculatorButton("ln", "log", variant="default")
                yield CalculatorButton("eˣ", "math.exp", variant="default")
                yield CalculatorButton("+/-", "-1 *", variant="default")

            # Stack operations
            with Horizontal(classes="button-row"):
                yield CalculatorButton("Pop", "pop", variant="success")
                yield CalculatorButton("Dup", "dup", variant="success")
                yield CalculatorButton("Swap", "swap", variant="success")
                yield CalculatorButton("Clear", "clear", variant="error")

    @on(Button.Pressed, "CalculatorButton")
    async def handle_calculator_button(self, event: Button.Pressed) -> None:
        """Handle calculator button presses."""
        # Prevent default button behavior to avoid focus issues
        event.prevent_default()

        # Clear any error notifications when user clicks a button
        self.clear_notifications()

        button = event.button
        assert isinstance(button, CalculatorButton)
        command = button.command

        input_field = self.query_one("#input-field", Input)

        # For digit and decimal point buttons, append to input field
        if command in "0123456789.":
            input_field.value += command
            input_field.cursor_position = len(input_field.value)
        elif command == "enter":
            # Enter button - submit current input
            if input_field.value.strip():
                self._execute_command(input_field.value.strip())
                input_field.value = ""
        else:
            # For operation buttons, first execute any pending input
            if input_field.value.strip():
                self._execute_command(input_field.value.strip())
                input_field.value = ""

            # Then execute the command
            # Handle multi-command sequences (separated by spaces)
            if " " in command:
                # Execute each command in sequence
                for cmd in command.split():
                    self._execute_command(cmd)
            else:
                self._execute_command(command)

    @on(Input.Changed, "#input-field")
    def handle_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes (typing)."""
        # Clear any error notifications when user starts typing
        # But only if they're actually adding content (not clearing)
        if event.value:
            self.clear_notifications()

    @on(Input.Submitted, "#input-field")
    def handle_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input field submission."""
        command = event.value.strip()
        if command:
            self._execute_command(command)
            event.input.value = ""
        else:
            # If Enter is pressed with empty input, just clear notifications
            self.clear_notifications()
        event.input.focus()

    def _execute_command(self, command: str) -> None:
        """Execute a calculator command and update displays."""
        stack_display = self.query_one("#stack-display", StackDisplay)
        variables_display = self.query_one("#variables-display", VariablesDisplay)

        try:
            if command == "clear":
                # Clear the stack
                self.calc.stack.clear()
                self.notify("Stack cleared", severity="information")
            else:
                # Execute the command through the calculator
                success = self.calc.execute(command)

                # Check if any errors were written to the error buffer
                error_output = self.error_buffer.getvalue().strip()

                if error_output:
                    # Display the error message from the calculator
                    self.notify(error_output, severity="error", timeout=5)
                elif not success:
                    self.notify("Command failed", severity="error")

            # Update displays
            stack_display.update_display()
            variables_display.update_display()

        except (CalculatorError, StackError) as e:
            self.notify(str(e), severity="error", timeout=5)
        except Exception as e:
            self.notify(f"Unexpected error: {e}", severity="error", timeout=5)
        finally:
            # Clear the error buffer for the next command
            self.error_buffer.truncate(0)
            self.error_buffer.seek(0)

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Set the theme
        self.theme = self.theme_name

        # Initialize the stack display
        stack_display = self.query_one("#stack-display", StackDisplay)
        stack_display.update_display()

        # Initialize the variables display
        variables_display = self.query_one("#variables-display", VariablesDisplay)
        variables_display.update_display()

        # Focus the input field so user can start typing immediately
        input_field = self.query_one("#input-field", Input)
        input_field.focus()

    def action_clear_input(self) -> None:
        """Clear the input field (bound to 'Escape' key)."""
        input_field = self.query_one("#input-field", Input)
        input_field.value = ""
        input_field.focus()


def run_tui(calc: Calculator, error_buffer: StringIO, theme: str = "nord") -> None:
    """Run the TUI application.

    Args:
        calc: The Calculator instance to use as the backend.
        error_buffer: The StringIO buffer used for capturing calculator errors.
        theme: The Textual theme to use (default: "nord").
    """
    app = CalculatorTUI(calc, error_buffer, theme=theme)
    app.run()
