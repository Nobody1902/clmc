import os


class ProgressBar:
    def __init__(self, title: str, max: int, keep: bool = True, unit: str = ""):
        self.title = title
        self.max = max
        self.progress = 0
        self.keep = keep
        self.unit = unit

    def __enter__(self):
        print()
        return self

    def __exit__(self, *kvargs):
        # Return back
        print("\x1b[F", end="")
        return self

    def __del__(self):
        if self.keep:
            print("\x1b[E", end="")
            return

        print("\x1b[2K", end="")

    def redraw(self):
        width = os.get_terminal_size().columns
        progress_percent_str = str(int(self.progress / self.max * 100))
        fraction_str = f" {self.progress}{self.unit}/{self.max}{self.unit} "

        bar_space = width - max(int((1 / 3) * width), 1) - 2 - 1 - 5 - len(fraction_str)
        bar_width = int((self.progress / self.max) * bar_space)

        if len(self.title) >= int((1 / 3) * width) - 2:
            self.title = self.title[: (int((1 / 3) * width) - 5)]
            self.title += "..."

        print(
            "\x1b[1F\x1b[2K",
            "\x1b[2K\r",
            self.title,
            # Spacing
            " " * max(int((1 / 3) * width) - len(self.title), 1),
            # Percent
            " " * (4 - len(progress_percent_str)),
            f"{progress_percent_str}% ",
            # Bar
            "[",
            # "\x1b[1m\x1b[47m#\x1b[0m" * bar_width,
            "#" * bar_width,
            " " * (bar_space - bar_width),
            "]",
            fraction_str,
            sep="",
            end="\n",
        )

    def update(self, amount: int):
        self.progress += amount

        self.redraw()
