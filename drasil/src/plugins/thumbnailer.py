import os.path as path
import os
from PIL import Image
import PIL
from ..drasil_context import DrasilContext

class DrasilPlug():
    hooks = ['thumbnailer']
    name = 'Thumbnailer'
    description = 'Create an img tag and the thumbnail of an image'
    help_str = 'You can insert an image using '
    help_str = '[$thumbnailer:img_path:thumb_width_px:img_caption$].'
    help_str += 'The thumbnail of the image will be created (width thumb_width_px) '
    help_str += 'and the image will have the caption img_caption. '
    help_str += 'The embedded thumb will ink to the original image. '

    def pre(self, *argv):
        pass

    def run(self, *argv):
        caller = path.split(argv[1].current_node)[-1]
        out_dir = argv[1].output_dir
        in_dir = argv[1].src_root

        img_link = argv[0][0]
        img_path = path.split(img_link)[0:-1][0]
        img_fixed_width = int(argv[0][1])
        img_caption = argv[0][2]
        img_name = path.split(img_link)[-1]
        thumb_name = 'thumb_' + img_name
        thumb_path = path.join(out_dir, img_path, thumb_name)
        thumb_link = path.join(img_path, thumb_name)
        thumb_folder = path.split(thumb_path)[0]
        if not path.isdir(thumb_folder):
            os.makedirs(thumb_folder)
        if not path.exists(thumb_path):
            image = Image.open(path.join(in_dir,img_link))
            width_percent = (img_fixed_width / float(image.size[0]))
            height_size = int((float(image.size[1]) * float(width_percent)))
            image = image.resize((img_fixed_width, height_size), PIL.Image.BICUBIC)
            image.save(thumb_path)
        img_tuple = (img_link, img_name, thumb_link, img_caption)
        out_str = '<div class="picture">'
        out_str += '    <a href="%s" alt="%s"><img src="%s">%s</a>' % img_tuple
        out_str += '</div>'
        return out_str

    def post(self, *argv):
        pass
