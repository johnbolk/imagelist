"""A managed collection of PhotoImages for use with Tkinter widgets.

This module provides the following class definition:

* ImageList - A managed collection of PhotoImages for use with Tkinter widgets
"""

__version__ = '1.3.5'

# pylint: disable=no-name-in-module
import io
import os
import math
from warnings import warn
from dataclasses import dataclass, asdict, field, replace
from typing import Any, Tuple, List, Dict, Union, Optional
from xdocument import XDocument, XElement
from cairo import ImageSurface, Context, Format, FillRule, Matrix
from pycairotk import LineCap, LineJoin, Antialias, Vector
from PIL.ImageTk import PhotoImage
from PIL import Image, ImageColor, UnidentifiedImageError
import numpy as np

try:
    import cairosvg  # type: ignore

    CAIRO_SVG = True
except OSError:
    CAIRO_SVG = False

NONE = (0.0, 0.0, 0.0, 0.0)
PI = math.pi


class ImageList:
    """A managed collection of PhotoImages for use with Tkinter widgets."""

    class Grayed:
        """A managed collection of grayed PhotoImages."""

        def __init__(self, parent: 'ImageList'):
            """Construct and initialize the collection."""
            self._image_list = parent
            self._grayed: List[PhotoImage] = parent._local.grayed

        def __len__(self) -> int:
            """Get the total number of images currently in the collection."""
            return len(self._grayed)

        def __iter__(self) -> Any:
            """Make the Grayed class an iterable collection."""
            return (image for image in self._grayed)

        def __getitem__(self, item: Union[int, str]) -> Any:
            """Get the grayed image with the given index value or key name."""
            result: Any = self._image_list.blank_image
            valid, index = self._image_list._find_index(item)
            if valid:
                result = self._grayed[index]
            else:
                self._image_list._warn_item(item)
            return result

    @dataclass
    class _Properties:
        """The ImageList properties."""

        resource_folder: str
        image_size: Tuple[int, int]
        images: List[PhotoImage] = field(default_factory=list)
        grayed: List[PhotoImage] = field(default_factory=list)
        keys: List[str] = field(default_factory=list)

    def __init__(
        self,
        resource_folder: str = '',
        image_size: Tuple[int, int] = (16, 16),
        auto_load: bool = False,
    ):
        """Construct and initialize the PhotoImage collection.

        Parameters
        ----------
        resource_folder : str
            The path of the resource file folder for image files, default = ''
        image_size : tuple[int, int]
            The size of the images in the collection, default = (16, 16) pixels
        auto_load : bool
            Automatically load all the resource folder's image files if True
        """
        width = max(1, min(image_size[0], 256))
        height = max(1, min(image_size[1], 256))
        image_size = (width, height)
        self._local = self._Properties(resource_folder, image_size)
        self._blank_image = PhotoImage(Image.new('RGBA', image_size, 0))
        if auto_load:
            self._verbose = False
            for file in sorted(os.listdir(resource_folder), key=str.lower):
                index = file.rfind('.')
                self.add(file, file[:index])
        self._verbose = True

    @property
    def blank_image(self) -> Any:
        """Get a blank (or transparent) image."""
        return self._blank_image

    @property
    def grayed(self) -> 'ImageList.Grayed':
        """Get the grayed PhotoImage collection."""
        return self.Grayed(self)

    @property
    def image_size(self) -> Tuple[int, int]:
        """Get the size of the images in the collection."""
        return self._local.image_size

    @property
    def keys(self) -> List[str]:
        """Get a list of the key names currently assigned to the images."""
        return list(self._local.keys)

    @property
    def resource_folder(self) -> str:
        """Get/Set the path of the resource file folder for image files."""
        return self._local.resource_folder

    @resource_folder.setter
    def resource_folder(self, path: str) -> None:
        """Get/Set the path of the resource file folder for image files."""
        self._local.resource_folder = path

    def __len__(self) -> int:
        """Get the total number of images currently in the collection."""
        return len(self._local.images)

    def __iter__(self) -> Any:
        """Make the ImageList class an iterable collection."""
        return (image for image in self._local.images)

    def __getitem__(self, item: Union[int, str, slice]) -> Any:
        """Get the image with the specified index value or key name."""
        image_list = ImageList(self.resource_folder, self.image_size)
        image = self._blank_image
        if isinstance(item, slice):
            try:
                grayed = self._local.grayed[item]
                images = self._local.images[item]
                keys = self._local.keys[item]
                for i, name in enumerate(keys):
                    image_list.update(grayed[i], images[i], name)
            except TypeError:
                warn("The slice indices must be integer values!", stacklevel=2)
        else:
            valid, index = self._find_index(item)
            if valid:
                image = self._local.images[index]
            else:
                self._warn_item(item)
        return image_list if isinstance(item, slice) else image

    def add(self, image_file: str, key_name: Optional[str] = None) -> bool:
        """Add an image with an optional key name to the end of the collection.

        Parameters
        ----------
        image_file : str
            The image file to add to the collection
        key_name : str
            The optional key name of the image (not case-sensitive)

        Returns
        -------
        bool
            True if the image was successfully added, False otherwise
        """
        success, image, grayed = self._get_image(image_file)
        if success:
            self._local.keys.append('' if key_name is None else key_name)
            self._local.images.append(image)
            self._local.grayed.append(grayed)
        return success

    def clear(self) -> None:
        """Remove all the images and keys from the collection."""
        self._local.keys.clear()
        self._local.images.clear()
        self._local.grayed.clear()

    def contains_key(self, name: str) -> bool:
        """Determine if the collection has an image with the specified key.

        Parameters
        ----------
        name : str
            The specified key name of the image (not case-sensitive)

        Returns
        -------
        bool
            True if the collection contains the key name, False otherwise
        """
        return self._find_index(name)[0]

    def extend(self, image_list: 'ImageList') -> bool:
        """Add a PhotoImage collection to the end of the current collection.

        The image_size property of the PhotoImage collection must match that of
        the current collection in order to be successfully added.

        Parameters
        ----------
        image_list : ImageList
            The PhotoImage collection.

        Returns
        -------
        bool
            True if the PhotoImage collection was added, False otherwise
        """
        valid = image_list.image_size == self.image_size
        if valid:
            for i, name in enumerate(image_list.keys):
                self.update(image_list.grayed[i], image_list[i], name)
        else:
            warn('The PhotoImage sizes do not Match!', stacklevel=2)
        return valid

    def index_of_key(self, name: str) -> int:
        """Return the zero-based index of the image with the specified key.

        Parameters
        ----------
        name : str
            The specified key name of the image (not case-sensitive)

        Returns
        -------
        int
            The index of the first occurrence of the key name, -1 otherwise
        """
        index = -1
        if name:
            key_lower = name.lower()
            for i, key in enumerate(self._local.keys):
                if key.lower() == key_lower:
                    index = i
                    break
        return index

    def remove_at(self, index: int) -> None:
        """Remove an image from the collection at the specified index.

        Parameters
        ----------
        index : int
            The zero-based index value of the image in the collection
        """
        if self._find_index(index)[0]:
            self._local.keys.pop(index)
            self._local.images.pop(index)
            self._local.grayed.pop(index)

    def remove_by_key(self, name: str) -> None:
        """Remove the image with the specified key name from the collection.

        Parameters
        ----------
        name : str
            The specified key name of the image (not case-sensitive)
        """
        valid, index = self._find_index(name)
        if valid:
            self.remove_at(index)

    def set_key_name(self, index: int, name: str) -> None:
        """Set the key name for an image in the collection.

        Parameters
        ----------
        index : int
            The zero-based index value of the image in the collection
        name : str
            The name to be set as the image's key name (not case-sensitive)
        """
        if self._find_index(index)[0]:
            self._local.keys[index] = name

    def update(self, grayed: PhotoImage, image: PhotoImage, key: str) -> None:
        """Update the grayed, image, and key lists."""
        self._local.grayed.append(grayed)
        self._local.images.append(image)
        self._local.keys.append(key)

    def _find_index(self, item: Any) -> Tuple[bool, int]:
        """Find the existence status and index value of the specified item."""
        index = -1
        count = len(self._local.images)
        if isinstance(item, int):
            index = item if item >= 0 else (count + item)
        elif isinstance(item, str):
            index = self.index_of_key(item)
        return 0 <= index < count, index

    def _get_image(self, filename: str) -> Tuple[bool, PhotoImage, PhotoImage]:
        """Try to obtain an image from the specified source."""
        file = os.path.join(self.resource_folder, filename)
        image = Image.new('RGBA', self.image_size, 0)
        success, message = False, f"'{filename}' is not a Valid Image File!"
        index = file.rfind('.')
        file = self._adjust_extension(file, index)
        if os.path.isfile(file):
            if file[index:].lower() == '.svg':
                image, success = self._svg_image(file, image)
            else:
                try:
                    image = Image.open(file).convert('RGBA')
                    success = True
                except UnidentifiedImageError:
                    pass
        else:
            message = f"The file: '{file}' does not Exist!"

        if self._verbose and not success:
            warn(message, stacklevel=3)

        if image.size != self.image_size:
            image = image.resize(self.image_size, Image.Resampling.LANCZOS)

        red, green, blue, alpha = image.split()
        grayed_alpha = alpha.point(lambda x: x * 0.35)
        grayed = Image.merge('RGBA', (red, green, blue, grayed_alpha))
        return success, PhotoImage(image), PhotoImage(grayed)

    @staticmethod
    def _svg_image(file: str, image: Image.Image) -> Tuple[Any, bool]:
        """Attempt to load a svg image file."""
        success = False
        if CAIRO_SVG:
            png_data = cairosvg.svg2png(url=file)  # type: ignore
            if png_data is not None:
                try:
                    image = Image.open(io.BytesIO(png_data))
                    success = True
                except UnidentifiedImageError:
                    pass
        else:  # Use the home-brewed version
            svg = LoadSVG(file)
            if svg.image is not None:
                image = svg.image
                success = True
        return image, success

    @staticmethod
    def _adjust_extension(file: str, index: int) -> str:
        """Adjust the file extension if necessary."""
        if index > 0:
            if not os.path.isfile(file):  # Try an upper case extension
                file = file[:index] + file[index:].upper()
                if not os.path.isfile(file):  # Try a lower case extension
                    file = file[:index] + file[index:].lower()
        return file

    @staticmethod
    def _warn_item(item: Union[int, str]) -> None:
        """Send a warning about an invalid index or key value."""
        label = 'index' if isinstance(item, (int, float)) else 'key'
        warn(f"'{item}' is not a valid {label} value!", stacklevel=3)


# pylint: disable=no-member
@dataclass
class Style:
    """The image rendering style parameters."""

    opacity: float = 1.0
    fill_rule: FillRule = FillRule.WINDING
    fill_opacity: float = 1.0
    fill: Tuple[float, ...] = (0.0, 0.0, 0.0, 1.0)
    stroke_linejoin: LineJoin = LineJoin.MITER
    stroke_linecap: LineCap = LineCap.BUTT
    stroke_dasharray: Tuple[float, ...] = ()
    stroke_opacity: float = 1.0
    stroke_width: float = 1.0
    stroke: Tuple[float, ...] = NONE


class LoadSVG:
    """A class for loading SVG image files."""

    _surface: ImageSurface
    _context: Context

    def __init__(self, filename: str):
        """Construct and initialize the class."""
        self._image = None
        self._style = Style()
        self._render_mode: Dict[int, Any] = {}
        self._parse_shapes: Dict[str, Any] = {
            'path': self._parse_path,
            'line': self._parse_line,
            'rect': self._parse_rect,
            'circle': self._parse_circle,
            'ellipse': self._parse_ellipse,
            'polygon': self._parse_polygon,
            'polyline': self._parse_polyline,
        }
        try:
            root_element = XDocument(filename).root
            if root_element.name == 'svg':
                self._init_image_area(root_element)
                self._process_group(root_element, self._style)
                self._image = self._construct_image()
        except (OSError, ZeroDivisionError, IndexError, ValueError):
            pass

    @property
    def image(self) -> Optional[Image.Image]:
        """Get the constructed PIL Image."""
        return self._image

    def _init_image_area(self, element: XElement) -> None:
        """Initialize the image area."""
        width = round(self._get_float(element.read_attribute('width')))
        height = round(self._get_float(element.read_attribute('height')))
        text = element.read_attribute('viewBox')
        if text:
            view_box = tuple(float(value) for value in text.split())
            aspect = view_box[2] / view_box[3]
        else:
            width = height if width == 0 else width
            height = width if height == 0 else height
            view_box = (0.0, 0.0, width, height)
            aspect = width / height

        size_x, size_y = round(128 * aspect), 128
        self._surface = ImageSurface(Format.ARGB32, size_x, size_y)
        self._context = Context(self._surface)
        self._context.set_antialias(Antialias.BEST)
        self._context.scale(size_x / view_box[2], size_y / view_box[3])
        self._context.translate(-view_box[0], -view_box[1])
        self._render_mode = {0: self._context.fill, 1: self._context.stroke}

    def _construct_image(self) -> Image.Image:
        """Construct a PIL Image."""
        shape = (self._surface.get_height(), self._surface.get_width(), 4)
        buffer = self._surface.get_data()
        buffer_array = np.ndarray(shape, np.uint8, buffer)  # type: ignore
        image_array = buffer_array.copy()
        image_array[:, :, 0] = buffer_array[:, :, 2]
        image_array[:, :, 2] = buffer_array[:, :, 0]
        return Image.fromarray(image_array)  # type: ignore

    def _process_group(self, element: XElement, style: Style) -> None:
        """Process the group attributes and children elements."""
        self._context.save()
        self._style = replace(style)
        self._read_transforms(element)
        self._read_style_parameters(element)
        group_style = replace(self._style)
        for child in element.children:
            if child.name == 'g':
                self._process_group(child, group_style)
            elif child.name in self._parse_shapes:
                self._process_shape(child, group_style)
        self._context.restore()

    def _process_shape(self, element: XElement, style: Style) -> None:
        """Process the given shape element."""
        self._context.save()
        self._style = replace(style)
        self._read_transforms(element)
        self._read_style_parameters(element)
        self._parse_shapes[element.name](element)
        self._context.restore()

    def _read_transforms(self, element: XElement) -> None:
        """Read and record the transform operations."""
        text = element.read_attribute('transform').replace(',', ' ').strip()
        while text:
            index = text.find('(')
            parameters = index + 1
            if index > 0:
                transform = text[:index]
                text = text[parameters:].lstrip()
                if transform == 'translate':
                    text = self._process_translate(text)
                elif transform == 'scale':
                    text = self._process_scale(text)
                elif transform == 'rotate':
                    text = self._process_rotate(text)
                elif transform in ('skewX', 'skewY', 'matrix'):
                    text = self._process_matrix(transform, text)
                else:  # Skip over any undefined transforms
                    index = text.find(')')
                    text = text[index:]
            text = text.lstrip(') ')

    def _process_translate(self, text: str) -> str:
        """Process a translation transform."""
        position_x, text = self._read_parameter(text)
        position_y = 0.0
        if text[0] != ')':
            position_y, text = self._read_parameter(text)
        self._context.translate(position_x, position_y)
        return text

    def _process_scale(self, text: str) -> str:
        """Process a scaling transform."""
        scale_x, text = self._read_parameter(text)
        scale_y = scale_x
        if text[0] != ')':
            scale_y, text = self._read_parameter(text)
        self._context.scale(scale_x, scale_y)
        return text

    def _process_rotate(self, text: str) -> str:
        """Process a rotation transform."""
        angle, text = self._read_parameter(text)
        position_x = position_y = 0.0
        if text[0] != ')':
            position_x, text = self._read_parameter(text)
            position_y, text = self._read_parameter(text)
        self._context.translate(position_x, position_y)
        self._context.rotate(math.radians(angle))
        self._context.translate(-position_x, -position_y)
        return text

    def _process_matrix(self, transform: str, text: str) -> str:
        """Process one of the matrix transforms."""
        matrix = Matrix()
        if transform == 'skewX':
            angle, text = self._read_parameter(text)
            matrix.xy = math.tan(math.radians(angle))
        elif transform == 'skewY':
            angle, text = self._read_parameter(text)
            matrix.yx = math.tan(math.radians(angle))
        else:  # transform == 'matrix':
            matrix.xx, text = self._read_parameter(text)
            matrix.yx, text = self._read_parameter(text)
            matrix.xy, text = self._read_parameter(text)
            matrix.yy, text = self._read_parameter(text)
            matrix.x0, text = self._read_parameter(text)
            matrix.y0, text = self._read_parameter(text)
        self._context.transform(matrix)
        return text

    def _read_style_parameters(self, element: XElement):
        """Read and optionally record the render style parameter values."""
        for name in element.attribute_names:
            if name == 'style':
                for text in element.read_attribute('style').split(';'):
                    text = text.replace(' ', '')
                    if text:
                        index = text.rfind(':')
                        parameter = index + 1
                        self._read_style(text[:index], text[parameter:])
            elif name.replace('-', '_') in asdict(self._style):
                self._read_style(name, element.read_attribute(name))
        self._set_style_parameters(self._style)

    def _read_style(self, name: str, text: str) -> None:
        """Read one of the render style attributes."""
        floats = ('opacity', 'fill_opacity', 'stroke_opacity', 'stroke_width')
        line_cap = {'butt': LineCap.BUTT, 'round': LineCap.ROUND}
        line_cap.update({'square': LineCap.SQUARE})
        line_join = {'round': LineJoin.ROUND, 'miter': LineJoin.MITER}
        line_join.update({'bevel': LineJoin.BEVEL})
        fill_rule = {'evenodd': FillRule.EVEN_ODD, 'nonzero': FillRule.WINDING}
        name = name.replace('-', '_')
        text = text.strip()
        if text:
            value: Any = None
            if name in floats:
                value = max(0.0, self._get_float(text))
            elif name in ('fill', 'stroke'):
                value = self._get_color(text)
            elif name == 'fill_rule':
                value = fill_rule.get(text)
            elif name == 'stroke_linejoin':
                value = line_join.get(text)
            elif name == 'stroke_linecap':
                value = line_cap.get(text)
            elif name == 'stroke_dasharray':
                if text != 'none':
                    text = text.strip().replace(',', ' ')
                    value = tuple(float(dash) for dash in text.split())
            if value is not None:
                setattr(self._style, name, value)

    def _set_style_parameters(self, style: Style) -> None:
        """Set the context render style parameters."""
        self._context.set_dash(style.stroke_dasharray)
        self._context.set_line_cap(style.stroke_linecap)
        self._context.set_line_join(style.stroke_linejoin)
        self._context.set_line_width(style.stroke_width)
        self._context.set_fill_rule(style.fill_rule)
        style.fill_opacity *= style.opacity
        style.stroke_opacity *= style.opacity
        if style.fill != NONE:
            style.fill = style.fill[:3] + (min(style.fill_opacity, 1.0),)
        if style.stroke != NONE:
            style.stroke = style.stroke[:3] + (min(style.stroke_opacity, 1.0),)

    def _parse_path(self, element: XElement) -> None:
        """Parse the path attributes."""
        for index, color in enumerate((self._style.fill, self._style.stroke)):
            if color != NONE:
                mirror = Vector(0, 0)
                self._context.move_to(0, 0)
                self._context_set_source_rgba(color)
                path = element.read_attribute('d').lstrip()
                while path:
                    mode, path = path[0], path[1:].lstrip()
                    if mode in ('M', 'm'):
                        path = self._path_move(mode, path)
                    elif mode in ('L', 'l', 'H', 'h', 'V', 'v'):
                        path = self._path_line(mode, path)
                    elif mode in ('C', 'c', 'S', 's'):
                        mirror, path = self._path_cubic(mode, mirror, path)
                    elif mode in ('Q', 'q', 'T', 't'):
                        mirror, path = self._path_quad(mode, mirror, path)
                    elif mode in ('A', 'a'):
                        path = self._path_arc(mode, path)
                    elif mode in ('Z', 'z'):
                        self._context.close_path()
                self._render_mode[index]()

    def _parse_line(self, element: XElement) -> None:
        """Parse the line attributes."""
        line: Dict[str, float] = {'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0}
        for name in line:
            if element.read_attribute(name):
                line[name] = float(element.read_attribute(name))
        self._context_set_source_rgba(self._style.stroke)
        self._context.move_to(line['x1'], line['y1'])
        self._context.line_to(line['x2'], line['y2'])
        self._context.stroke()

    def _parse_rect(self, element: XElement) -> None:
        """Parse the rectangle attributes."""
        rect: Dict[str, float] = {'x': 0, 'y': 0, 'width': 0, 'height': 0}
        rect.update({'rx': 0, 'ry': 0})
        for name in rect:
            if element.read_attribute(name):
                rect[name] = float(element.read_attribute(name))
        for index, color in enumerate((self._style.fill, self._style.stroke)):
            if color != NONE:
                self._context_set_source_rgba(color)
                if rect['rx'] == 0 and rect['ry'] == 0:
                    self._context.rectangle(
                        rect['x'], rect['y'], rect['width'], rect['height']
                    )
                else:
                    rect['rx'] = rect['ry'] if rect['rx'] == 0 else rect['rx']
                    rect['ry'] = rect['rx'] if rect['ry'] == 0 else rect['ry']
                    radius = Vector(abs(rect['rx']), abs(rect['ry']))
                    start = Vector(rect['x'], rect['y'])
                    if rect['width'] < 0:
                        start += Vector(rect['width'], 0)
                    if rect['height'] < 0:
                        start += Vector(0, rect['height'])
                    size = Vector(abs(rect['width']), abs(rect['height']))
                    radius.x = min(radius.x, size.x / 2)
                    radius.y = min(radius.y, size.y / 2)
                    position_0 = Vector(start.x + radius.x, start.y)
                    self._context.move_to(position_0.x, position_0.y)
                    line_end = [
                        start + Vector(size.x - radius.x, 0),
                        start + Vector(size.x, size.y - radius.y),
                        start + Vector(radius.x, size.y),
                        start + Vector(0, radius.y),
                    ]
                    arc_end = [
                        start + Vector(size.x, radius.y),
                        start + Vector(size.x - radius.x, size.y),
                        start + Vector(0, size.y - radius.y),
                        position_0,
                    ]
                    for i in range(4):
                        self._context_line_to(line_end[i])
                        self._render_arc(radius, arc_end[i])
                self._render_mode[index]()

    def _parse_circle(self, element: XElement) -> None:
        """Parse the circle attributes."""
        circle: Dict[str, float] = {'r': 0, 'cx': 0, 'cy': 0}
        for name in circle:
            if element.read_attribute(name):
                circle[name] = float(element.read_attribute(name))
        self._context.translate(circle['cx'], circle['cy'])
        for index, color in enumerate((self._style.fill, self._style.stroke)):
            if color != NONE:
                self._context_set_source_rgba(color)
                self._context.arc(0, 0, abs(circle['r']), 0, 2 * PI)
                self._render_mode[index]()

    def _parse_ellipse(self, element: XElement) -> None:
        """Parse the ellipse attributes."""
        ellipse: Dict[str, float] = {'rx': 0, 'ry': 0, 'cx': 0, 'cy': 0}
        for name in ellipse:
            if element.read_attribute(name):
                ellipse[name] = float(element.read_attribute(name))
        self._context.translate(ellipse['cx'], ellipse['cy'])
        width, height = abs(ellipse['rx']), abs(ellipse['ry'])
        self._context.scale(width, height)
        scale_factor = 2 / (width + height)
        self._context.set_line_width(scale_factor * self._style.stroke_width)
        for index, color in enumerate((self._style.fill, self._style.stroke)):
            if color != NONE:
                self._context_set_source_rgba(color)
                self._context.arc(0, 0, 1, -PI, PI)
                self._render_mode[index]()

    def _parse_polygon(self, element: XElement) -> None:
        """Parse the polygon points attribute."""
        self._parse_polyline(element, close=True)

    def _parse_polyline(self, element: XElement, close: bool = False) -> None:
        """Parse the polyline points attribute."""
        points: List[Vector] = []
        text = element.read_attribute('points').replace(',', ' ')
        while text:
            point, text = self._read_position(text)
            points.append(point)
        for index, color in enumerate((self._style.fill, self._style.stroke)):
            if color != NONE:
                self._context_set_source_rgba(color)
                self._context.move_to(points[0].x, points[0].y)
                for point in points[1:]:
                    self._context_line_to(point)
                if close:
                    self._context.close_path()
                self._render_mode[index]()

    def _path_move(self, mode: str, text: str) -> str:
        """Process the path move modes."""
        point, text = self._read_position(text, mode)
        self._context.move_to(point.x, point.y)
        while text and not text[0].isalpha():
            point, text = self._read_position(text, mode)
            self._context_line_to(point)
        return text

    def _path_line(self, mode: str, text: str) -> str:
        """Process the path line modes."""
        while text and not text[0].isalpha():
            if mode in ('L', 'l'):
                point, text = self._read_position(text, mode)
            else:
                current = self._context_get_current_point()
                coord, text = self._read_coordinate(text)
                if mode in ('H', 'h'):
                    coord += 0 if mode == 'H' else current.x
                    point = Vector(coord, current.y)
                else:
                    coord += 0 if mode == 'V' else current.y
                    point = Vector(current.x, coord)
            self._context_line_to(point)
        return text

    def _path_cubic(
        self, mode: str, mirror: Vector, text: str
    ) -> Tuple[Vector, str]:
        """Process the path cubic curve modes."""
        while text and not text[0].isalpha():
            current = self._context_get_current_point()
            pnt = [mirror, mirror, mirror]
            if mode in ('C', 'c'):
                pnt[0], text = self._read_position(text, mode)
            else:
                pnt[0] += current
            pnt[1], text = self._read_position(text, mode)
            pnt[2], text = self._read_position(text, mode)
            mirror = pnt[2] - pnt[1]
            self._context.curve_to(
                pnt[0].x, pnt[0].y, pnt[1].x, pnt[1].y, pnt[2].x, pnt[2].y
            )
        return mirror, text

    def _path_quad(
        self, mode: str, mirror: Vector, text: str
    ) -> Tuple[Vector, str]:
        """Process the path quadratic curve modes."""
        while text and not text[0].isalpha():
            current = self._context_get_current_point()
            if mode in ('Q', 'q'):
                quad_0, text = self._read_position(text, mode)
            else:
                quad_0 = current + mirror
            quad_1, text = self._read_position(text, mode)
            mirror = quad_1 - quad_0
            peak = 2 * quad_0
            pnt = [(current + peak) / 3, (quad_1 + peak) / 3, quad_1]
            self._context.curve_to(
                pnt[0].x, pnt[0].y, pnt[1].x, pnt[1].y, pnt[2].x, pnt[2].y
            )
        return mirror, text

    def _path_arc(self, mode: str, text: str) -> str:
        """Process the path elliptical arc modes."""
        while text and not text[0].isalpha():
            radius, text = self._read_position(text)
            rotate, text = self._read_coordinate(text)
            value, text = self._read_coordinate(text)
            large_arc = bool(int(value))
            value, text = self._read_coordinate(text)
            sweep = bool(int(value))
            end, text = self._read_position(text, mode)
            start = self._context_get_current_point()
            if end != start and radius.x != 0 and radius.y != 0:
                self._render_arc(radius, end, rotate, sweep, large_arc)
            else:
                self._context_line_to(end)
        return text

    def _render_arc(
        self,
        radius: Vector,
        end: Vector,
        angle: float = 0.0,
        sweep: bool = True,
        large_arc: bool = False,
    ) -> None:
        """Render the specified elliptical arc segment."""
        sweep = not sweep if large_arc else sweep
        center, begin, stop = self._find_center(radius, end, angle, sweep)
        if sweep:  # Positive sweep direction
            if stop < begin:
                stop = (stop + 2 * PI) % (2 * PI)
            interval = stop - begin
            if large_arc:
                interval -= 2 * PI
        else:  # Negative sweep direction
            if begin < stop:
                begin = (begin + 2 * PI) % (2 * PI)
            interval = stop - begin
            if large_arc:
                interval += 2 * PI
        delta = math.copysign(PI / 20, interval)
        for i in range(1, math.ceil(interval / delta)):
            phi = begin + i * delta
            arc = Vector(radius.x * math.cos(phi), radius.y * math.sin(phi))
            self._context_line_to((center + arc).rotated(angle))
        self._context_line_to(end)

    def _find_center(
        self, radius: Vector, end: Vector, angle: float, sweep: bool
    ) -> Tuple[Vector, float, float]:
        """Find the center location and the two angles of the arc."""
        start = self._context_get_current_point()
        start = start.rotated(-angle)
        end = end.rotated(-angle)
        chord = end - start
        radius.x = max(abs(chord.x) / 2, abs(radius.x))
        radius.y = max(abs(chord.y) / 2, abs(radius.y))
        chord = Vector(chord.x / radius.x, chord.y / radius.y)
        mid_point = chord / 2
        length = math.sqrt((1 / mid_point.length) ** 2 - 1)
        center = mid_point + length * mid_point.rotated(90 if sweep else -90)
        begin = math.atan2(-center.y, -center.x)
        stop = math.atan2(chord.y - center.y, chord.x - center.x)
        center = start + Vector(radius.x * center.x, radius.y * center.y)
        return center, begin, stop

    def _context_line_to(self, position: Vector) -> None:
        """Execute the context line_to method."""
        self._context.line_to(position.x, position.y)

    def _context_set_source_rgba(self, color: Tuple[float, ...]) -> None:
        """Set the context source rgba color."""
        self._context.set_source_rgba(color[0], color[1], color[2], color[3])

    def _context_get_current_point(self) -> Vector:
        """Get the current context point as a Vector."""
        x_coord, y_coord = self._context.get_current_point()
        return Vector(x_coord, y_coord)

    def _read_position(self, text: str, mode: str = 'A') -> Tuple[Vector, str]:
        """Read the absolute position value and update the text string."""
        x_coord, text = self._read_coordinate(text)
        y_coord, text = self._read_coordinate(text)
        position = Vector(x_coord, y_coord)
        if mode.islower():
            position += self._context_get_current_point()
        return position, text

    @staticmethod
    def _read_coordinate(text: str) -> Tuple[float, str]:
        """Read the coordinate value and update the text string."""
        try:
            index = 1 if text[0] == '-' else 0
            char = text[index]
            period = False
            while char.isdecimal() or (not period and char == '.'):
                period |= char == '.'
                index += 1
                if index < len(text):
                    char = text[index]
                else:
                    break
            try:
                value, text = float(text[:index]), text[index:].lstrip(', ')
            except ValueError:
                value, text = 0.0, text[index:].lstrip(', ')
        except IndexError:
            value, text = 0.0, ''
        return value, text

    @staticmethod
    def _read_parameter(text: str) -> Tuple[float, str]:
        """Read the parameter value and update the text string."""
        try:
            index = 0
            while index < len(text) and text[index] not in (' ', ')'):
                index += 1
            try:
                value, text = float(text[:index]), text[index:].lstrip()
            except ValueError:
                value, text = 0.0, text[index:].lstrip()
        except IndexError:
            value, text = 0.0, ''
        return value, text

    @staticmethod
    def _get_float(text: str) -> float:
        """Get a valid and scaled floating point value."""
        text = text.strip()
        try:
            index = -1
            if text[index] == '%':
                value = float(text[:index]) / 100
            elif text[index].isalpha():
                while text[index].isalpha():
                    index -= 1
                index += 1
                value = float(text[:index])
            else:
                value = float(text)
        except (IndexError, ValueError):
            value = 0.0
        return value

    @staticmethod
    def _get_color(color: str) -> Tuple[float, ...]:
        """Convert the color string to a tuple."""
        try:
            rgb_color = ImageColor.getrgb(color)[:3] + (255,)
            result = tuple((component / 255) for component in rgb_color)
        except ValueError:
            result = NONE
        return result
