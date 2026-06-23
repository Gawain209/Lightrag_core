"""Legacy Word (.doc) binary format parser.

Uses olefile to extract text from Word Binary Format (OLE2 compound documents).
Parses the FIB (File Information Block) and piece table to locate document text.
"""

import struct
from pathlib import Path

from lightrag_core.ingestion.parser import BaseParser


class DocParser(BaseParser):
    """Parser for legacy .doc (Word 97-2003) files via OLE2 binary format.

    Extracts text by parsing the FIB and walking the piece table in the
    WordDocument stream. For modern .docx files, use WordParser instead.
    """

    SUPPORTED_EXTENSIONS = {".doc"}

    def parse(self, file_path: str | Path) -> str:
        try:
            import olefile
        except ImportError:
            raise RuntimeError(
                "olefile required for .doc parsing: pip install olefile"
            )

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            ole = olefile.OleFileIO(str(path))
            return self._extract_text(ole)
        except Exception as e:
            raise RuntimeError(f"Failed to parse .doc file: {e}")

    def _extract_text(self, ole) -> str:
        word_stream = ole.openstream("WordDocument").read()

        w_ident = struct.unpack_from("<H", word_stream, 0x0000)[0]
        if w_ident != 0xA5EC:
            raise ValueError("Not a valid Word binary document")

        n_fib = struct.unpack_from("<H", word_stream, 0x0002)[0]
        flags = struct.unpack_from("<H", word_stream, 0x000A)[0]
        f_which_tbl_stm = (flags >> 9) & 1

        fc_clx = struct.unpack_from("<I", word_stream, 0x01A2)[0]
        lcb_clx = struct.unpack_from("<I", word_stream, 0x01A6)[0]

        table_name = "1Table" if f_which_tbl_stm else "0Table"

        try:
            table_stream = ole.openstream(table_name).read()
        except Exception:
            return self._fallback_extract(word_stream)

        clx_data = table_stream[fc_clx : fc_clx + lcb_clx]
        pieces = self._parse_piece_table(clx_data)

        if not pieces:
            return self._fallback_extract(word_stream)

        lines: list[str] = []
        for fc, ccp in pieces:
            try:
                chunk = word_stream[fc : fc + ccp * 2]
                text = chunk.decode("utf-16-le", errors="replace")
            except Exception:
                continue
            cleaned = "".join(
                c if c.isprintable() or c in "\n\r\t" else " "
                for c in text
            )
            if cleaned.strip():
                lines.append(cleaned)

        ole.close()
        return "\n".join(lines)

    def _parse_piece_table(self, clx_data: bytes) -> list[tuple[int, int]]:
        """Parse Pcdt entries from Clx data. Returns list of (fc, ccp) tuples."""
        pos = 0
        # Skip Prc (Property revision)
        if pos < len(clx_data):
            cb_grpprl = clx_data[pos]
            pos += 1 + cb_grpprl

        if pos + 4 > len(clx_data):
            return []

        lcb = struct.unpack_from("<I", clx_data, pos)[0]
        pos += 4

        if lcb == 0 or pos + lcb > len(clx_data):
            return []

        plcpcd = clx_data[pos : pos + lcb]
        entry_size = 12  # 4 bytes CP + 8 bytes Pcd
        num_pcds = lcb // entry_size - 1  # n+1 CPs, n Pcds

        pieces = []
        for i in range(num_pcds):
            cp_start = struct.unpack_from("<I", plcpcd, i * entry_size)[0]
            cp_end = struct.unpack_from("<I", plcpcd, (i + 1) * entry_size)[0]
            pcd_fc = struct.unpack_from("<I", plcpcd, i * entry_size + 4)[0]
            # prm = struct.unpack_from("<I", plcpcd, i * entry_size + 8)[0]

            if pcd_fc & 0x40000000:
                fc = pcd_fc & ~0x40000000
            else:
                fc = pcd_fc

            ccp = cp_end - cp_start
            if fc > 0 and ccp > 0 and ccp < 100000:
                pieces.append((fc, ccp))

        return pieces

    def _fallback_extract(self, word_stream: bytes) -> str:
        """Heuristic fallback: decode WordDocument stream as UTF-16LE text."""
        text = word_stream.decode("utf-16-le", errors="replace")
        lines = []
        for line in text.split("\n"):
            cleaned = "".join(
                c if c.isprintable() or c in "\n\r\t" else "" for c in line
            )
            if len(cleaned) > 3:
                lines.append(cleaned.strip())
        return "\n".join(lines[:500])

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
