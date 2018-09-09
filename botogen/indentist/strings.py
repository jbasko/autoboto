def join_lines(*lines):
    """
    Join lines with "\n", but skip lines that are None.

    This is useful when generating lines in conditional code:

        join_lines(
            "import logging" if "logging" in imports else None,
        )

    """
    return "\n".join(line for line in lines if line is not None)
