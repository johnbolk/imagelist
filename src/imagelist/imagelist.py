"""A managed collection of PhotoImages for use with Tkinter widgets.

This module provides the following class definition:

* ImageList - A managed collection of PhotoImages for use with Tkinter widgets
"""

__version__ = '1.2.0'

import os
from warnings import warn
from dataclasses import dataclass, field
from typing import Any, Tuple, List, Union, Optional
from PIL.ImageTk import PhotoImage
from PIL import Image, UnidentifiedImageError


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
        success, image = False, Image.new('RGBA', self.image_size, 0)
        file = os.path.join(self.resource_folder, filename)
        index = file.rfind('.')
        if index > 0:
            if not os.path.isfile(file):  # Try an upper case extension
                file = file[:index] + file[index:].upper()
                if not os.path.isfile(file):  # Try a lower case extension
                    file = file[:index] + file[index:].lower()
        if os.path.isfile(file):
            try:
                image = Image.open(file).convert('RGBA')
                success = True
            except UnidentifiedImageError:
                if self._verbose:
                    warn(f"'{filename}' is not an Image File!", stacklevel=3)
        else:
            warn(f"The file: '{file}' does not Exist!", stacklevel=3)

        if image.size != self.image_size:
            image = image.resize(self.image_size, Image.Resampling.LANCZOS)

        red, green, blue, alpha = image.split()
        grayed_alpha = alpha.point(lambda x: x * 0.35)
        grayed = Image.merge('RGBA', (red, green, blue, grayed_alpha))
        return success, PhotoImage(image), PhotoImage(grayed)

    @staticmethod
    def _warn_item(item: Union[int, str]) -> None:
        """Send a warning about an invalid index or key value."""
        label = 'index' if isinstance(item, (int, float)) else 'key'
        warn(f"'{item}' is not a valid {label} value!", stacklevel=3)
