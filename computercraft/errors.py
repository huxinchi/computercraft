from typing import Optional

class LuaException(Exception):
    @property
    def message(self) -> Optional[str]:
        if len(self.args) < 1:
            return None
        return self.args[0]