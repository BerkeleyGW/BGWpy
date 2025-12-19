from __future__ import annotations

from typing import Any

from BGWpy.core import Namelist

__all__ = ["PW2WanInput"]


class PW2WanInput(Namelist):
    def __init__(
        self,
        prefix: str,
        outdir: str = "./",
        write_amn: bool = True,
        write_mmn: bool = True,
        seedname: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            "inputpp",
            [
                ("prefix", prefix),
                ("outdir", outdir),
                ("seedname", seedname if seedname else prefix),
                ("write_amn", write_amn),
                ("write_mmn", write_mmn),
            ],
            **kwargs,
        )
