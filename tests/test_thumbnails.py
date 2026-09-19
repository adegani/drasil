import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image

from drasil.src.drasil import clean_output
from drasil.src.plugins.thumbnailer import DrasilPlug


class ThumbnailTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.output = self.root / 'output'
        (self.source / 'assets').mkdir(parents=True)
        self.output.mkdir()
        self.original = self.source / 'assets' / 'photo.jpg'
        self.thumbnail = self.output / 'assets' / 'thumb_photo.jpg'
        self.write_image('red')
        self.context = SimpleNamespace(src_root=str(self.source), output_dir=str(self.output))

    def write_image(self, color):
        with Image.new('RGB', (100, 50), color) as image:
            image.save(self.original)

    def render(self, width=20):
        return DrasilPlug().run(['assets/photo.jpg', str(width), 'Caption'], self.context)

    def test_cleanup_preserves_nested_thumbnails_without_following_symlinks(self):
        self.render()
        before = self.thumbnail.read_bytes()
        (self.output / 'index.html').write_text('old page')
        (self.output / 'assets' / 'photo.jpg').write_bytes(b'old original')
        (self.output / 'empty').mkdir()
        (self.output / 'thumb_directory').mkdir()
        (self.output / 'thumb_directory' / 'old.html').write_text('old page')
        (self.output / 'linked').symlink_to(self.source, target_is_directory=True)
        (self.output / 'thumb_link.jpg').symlink_to(self.original)
        (self.output / 'thumb_broken.jpg').symlink_to(self.root / 'missing')

        clean_output(self.output)

        self.assertEqual(self.thumbnail.read_bytes(), before)
        self.assertTrue(self.original.is_file())
        self.assertEqual(
            {p.relative_to(self.output).as_posix() for p in self.output.rglob('*')},
            {'assets', 'assets/thumb_photo.jpg'},
        )

    def test_rebuild_reuses_thumbnail_without_resizing(self):
        self.render()
        before = self.thumbnail.stat().st_mtime_ns
        clean_output(self.output)
        with patch.object(Image.Image, 'resize', side_effect=AssertionError('unexpected resize')):
            html = self.render()
        self.assertIn('assets/thumb_photo.jpg', html)
        self.assertEqual(self.thumbnail.stat().st_mtime_ns, before)

    def test_changed_width_regenerates_thumbnail(self):
        self.render()
        self.render(width=40)
        with Image.open(self.thumbnail) as thumbnail:
            self.assertEqual(thumbnail.size, (40, 20))

    def test_newer_source_regenerates_thumbnail(self):
        self.render()
        self.write_image('blue')
        older = self.original.stat().st_mtime_ns - 1_000_000_000
        os.utime(self.thumbnail, ns=(older, older))
        self.render()
        with Image.open(self.thumbnail) as thumbnail:
            red, _, blue = thumbnail.getpixel((0, 0))
            self.assertGreater(blue, red)

    def test_unreadable_thumbnail_is_regenerated(self):
        self.render()
        self.thumbnail.write_bytes(b'broken image')
        self.render()
        with Image.open(self.thumbnail) as thumbnail:
            self.assertEqual(thumbnail.size, (20, 10))


if __name__ == '__main__':
    unittest.main()
