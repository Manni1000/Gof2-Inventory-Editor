from AEPi import AEI
from typing import Dict, Iterable, List, Optional
import os
from os.path import join
from enum import Enum

class ItemIconResolution(Enum):
    SD = 0
    IPhone4 = 1
    IPad = 2
    IPad_1440 = 3
    IPad_large = 4

# A list of file name segments. See the item_icons_aei_file_name function for usage.
ITEM_ICONS_AEI_RESOLUTIONS = {
    ItemIconResolution.SD:         ("", ""),
    ItemIconResolution.IPhone4:    ("iphone4", ""),
    ItemIconResolution.IPad:       ("ipad", ""),
    ItemIconResolution.IPad_1440:  ("ipad", "1440"),
    ItemIconResolution.IPad_large: ("ipad", "large")
}

# Directory scanning sanity check
MAX_ITEM_ICONS_AEIS_PER_RESOLUTION = 99

# 176 items per AEI
# This is needed because the first 'items' AEI contains more than just items!
ITEM_ICONS_AEI_CHUNK_SIZE = 176

def _underscoreTruthy(s):
        return f"_{s}" if s else ""

def item_icons_aei_file_name(resolution: ItemIconResolution, aei_index: int):
    prefix, suffix = ITEM_ICONS_AEI_RESOLUTIONS[resolution]    

    return "".join((
        "gof2_items",
        _underscoreTruthy(prefix),
        '' if aei_index == 1 else f"_{aei_index}",
        _underscoreTruthy(suffix),
        ".aei"))


class Gof2ItemIcons:
    def __init__(self, aei_paths: Iterable[str]) -> None:
        self.aei_paths = list(aei_paths)
        self._lazy_aeis: List[Optional[AEI]] = [None] * len(self.aei_paths)


    def _get_aei(self, aei_index: int):
        if existing := self._lazy_aeis[aei_index]:
            return existing
        
        aei = AEI.read(self.aei_paths[aei_index])
        self._lazy_aeis[aei_index] = aei
        return aei


    def get_aei(self, item_id: int):
        aei_index = int(item_id / ITEM_ICONS_AEI_CHUNK_SIZE)
        if aei_index >= len(self._lazy_aeis):
            raise KeyError(f"No AEI is stored for item with id {item_id}")
        
        return self._get_aei(aei_index)
        

    def get_image(self, item_id: int):
        aei = self.get_aei(item_id)
        texture_index = item_id % ITEM_ICONS_AEI_CHUNK_SIZE
        texture = aei.textures[texture_index]
        return aei.getTexture(texture)


    def close(self):
        for aei in self._lazy_aeis:
            if aei:
                aei.close()


    def __del__(self):
        self.close()


class Gof2Installation:
    def __init__(self, base_path: str) -> None:
        self.base_path = base_path
        self._item_icon_resolutions: Dict[ItemIconResolution, Optional[Gof2ItemIcons]] = {
            resolution: None for resolution in ItemIconResolution
        }
        self._discover_textures()


    @property
    def data_folder(self):
        return join(self.base_path, "data")

    
    def _discover_textures(self):
        textures_folder = join(self.data_folder, "textures")

        for resolution in ItemIconResolution:
            aei_path = join(textures_folder, item_icons_aei_file_name(resolution, 1))
            if not os.path.isfile(aei_path):
                self._item_icon_resolutions[resolution] = None
                continue

            resolution_paths = [aei_path]
            for aei_index in range(2, MAX_ITEM_ICONS_AEIS_PER_RESOLUTION):
                current_path = join(textures_folder, item_icons_aei_file_name(resolution, aei_index))
                if not os.path.isfile(current_path):
                    break
                resolution_paths.append(current_path)

            self._item_icon_resolutions[resolution] = Gof2ItemIcons(resolution_paths)


    def item_icons(self, resolution: Optional[ItemIconResolution] = None):
        """Get the item icons AEI(s) in the installation, at a particular resolution.
        If no resolution is specified, the highest available resolution is returned.
        
        :param resolution: The item icon resolution to get, defaults to maximum available resolution
        :type resolution: Optional[ItemIconResolution], optional
        :raises ValueError: If `resolution` was not given, but no item icons AEIs exist in the installation
        :raises KeyError: If `resolution` does not exist in the installation
        """
        if resolution is None:
            resolution = max((r for r, t in self._item_icon_resolutions.items() if t), key=lambda r: r.value, default=None)
            if resolution is None:
                raise ValueError("No item icons AEIs were found in the installation")

        icons = self._item_icon_resolutions.get(resolution, None)
        if icons is None:
            raise KeyError(f"The resolution was not found in the installation: {resolution}")
        
        return icons
    

    def close(self):
        for item_icons in self._item_icon_resolutions.values():
            if item_icons:
                item_icons.close()


    def __del__(self):
        self.close()
