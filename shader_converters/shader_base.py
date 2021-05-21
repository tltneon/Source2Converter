import os
from collections import defaultdict
from pathlib import Path

from PIL import Image

from SourceIO.bpy_utilities.logging import BPYLoggingManager
from SourceIO.source1.vmt.valve_material import VMT
from SourceIO.source1.vtf.VTFWrapper import VTFLib
from SourceIO.source_shared.content_manager import ContentManager
from SourceIO.utilities.keyvalues import KVWriter

log_manager = BPYLoggingManager()


class ShaderBase:
    vtf_lib = VTFLib.VTFLib()

    def __init__(self, name, sub_path, vmt: VMT, output_path: Path):
        self.name = name
        self.sub_path = sub_path
        self._vmt = vmt
        self._material = self._vmt.material
        self._output_path = output_path
        self._textures = {}
        self._vmat_params = {'shader': 'vr_complex.vfx', 'F_MORPH_SUPPORTED': 1}

        self.logger = log_manager.get_logger(self.__class__.__name__)

    def convert(self):
        raise NotImplemented('Implement me')

    @staticmethod
    def _write_vector(array):
        return f"[{' '.join(map(str, array))}]"

    def write_vmat(self):
        save_path = self._output_path / 'materials' / self.sub_path / f'{self.name}.vmat'
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open('w') as file:
            file.write('// Generated by Source2Converter\r\n')
            writer = KVWriter(file)
            writer.write(('Layer0', self._vmat_params))

    def load_texture(self, texture_path):
        content_manager = ContentManager()
        self.logger.info(f"Loading texture {texture_path}")
        texture_path = content_manager.find_texture(texture_path)
        if texture_path and self.vtf_lib.image_load_from_buffer(texture_path.read()):
            texture = Image.frombytes("RGBA", (self.vtf_lib.width(), self.vtf_lib.height()),
                                      self.vtf_lib.get_rgba8888().contents)
            return texture
        else:
            self.logger.error(f"Texture {texture_path} not found!")
        return None

    @staticmethod
    def _write_settings(filename: Path, props: dict):
        with filename.open('w') as settings:
            settings.write('"settings"\n{\n')
            for _key, _value in props.items():
                settings.write(f'\t"{_key}"\t{_value}\n')
            settings.write('}\n')

    def write_texture(self, image: Image.Image, suffix='unk', settings=None):
        save_path = self._output_path / 'materials' / self.sub_path
        os.makedirs(save_path, exist_ok=True)
        save_path /= f'{self.name}_{suffix}.tga'
        self.logger.info(f'Wrote texture to {save_path}')
        image.save(save_path)
        if settings is not None and isinstance(settings, dict):
            self._write_settings(save_path.with_suffix('.txt'), settings)
        return str(save_path.relative_to(self._output_path))

    @staticmethod
    def ensure_length(array: list, length, filler):
        if len(array) < length:
            return array.extend([filler] * length - len(array))
        elif len(array) > length:
            return array[:length]
        return array