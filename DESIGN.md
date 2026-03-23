# REQUIREMENTS AND DESIGN NOTES

## Files, Node Types, and Source Directory Structure

### File Types

| File       | Node Type    | Notes                                       |
|------------|--------------|---------------------------------------------|
| index.md   | HOME or PAGE | index.md at root is HOME, otherwise PAGE    |
| index.html | HOME or PAGE | index.html at root is HOME, otherwise PAGE  |
| index.htm  | HOME or PAGE | index.htm at root is HOME, otherwise PAGE   |
| *.md       | PAGE         | any other .md file is PAGE                  |
| *.html     | PAGE         | any other .html file is PAGE                |
| *.htm      | PAGE         | any other .html file is PAGE                |
| *.jpg      | IMAGE        |                                             |
| *.jpeg     | IMAGE        |                                             |
| *.png      | IMAGE        |                                             |
| *.webp     | IMAGE        |                                             |
| ~*.avif~   | ~IMAGE~      | no `pyexif2` support; **skip for now**      |
| *.conf     | CONFIG       | unless site.conf, ignored for now           |
| *.config   | CONFIG       | unless site.config, ignored for now         |
| *          | STATIC       | Anything that doesn't match above is STATIC |

Markdown files (.md) are processed as markdown. HTML files (.html or .htm) are
copied into the appropriate target directory (with a name change to
`index.html` if needed for pretty URLs) with no other processing.

### Node Types

#### Home

- Directory: **yes**
- Type: **HOME**
- Template: `home.html`

The root of the site is of type **HOME**, regardless of whether there's an
index file or not. This is useful because the home page may want to use a
different template or otherwise behave differently than other pages. For
example, the default template often includes *both* the site title and the page
title in the `<title>` element, but the home page may only want to include the
site title.

If there's an index file in the source root, then that's used to generate the
content for the root `index.html` page. If there's no index file, or if the
index file is empty, then a directory listing should be added automatically
(perhaps by automatically inserting a `listing.html` shortcode template).

### Single Pages

- Directory: **no**
- Type: **PAGE**
- Template: `page.html`

Any page that is not an index file is a single page. By default, this should be
rendered as a pretty URL, so, for example, `colophon.md` becomes
`colophon/index.html`.

### Page Bundles

- Directory: **yes**
- Type: **PAGE**
- Template: `page.html`

Any directory (other than the source root) that contains an index file is also
of type **PAGE**. In this case, a pretty URL is already effectively setup, so,
for example, `about/index.md` becomes `about/index.html`. These should also use
the `page.html` template.

**NOTE**: This should be true *even if* the directory contains only images
(aside from the index file). In the past, such a directory would have been
treated as a GALLERY, but that's undesirable in a number of cases, and we can
treat the inclusion of an index file as a signal that the user wants more
control over the content and layout of the page.

### Images

- Directory: **no**
- Type: **IMAGE**
- Template: `image.html`

By default (for now) images generate a pretty URL page for each image. So for
example, `photo1.jpg` generates a page at `photo1/index.html` largely
containing information pulled from the image's metadata.

### Static Files

- Directory: **no**
- Type: **STATIC**
- Template: n/a

Any individual file that is not an image or content file (markdown or html) is
a static file. Static files are simply copied from the source tree to the
target tree with no processing.

### Galleries

- Directory: **yes**
- Type: **GALLERY**
- Template: `gallery.html`

A directory that contains nothing but image files is of type **GALLERY**. A
special type is warranted here to make it easier build a visual layout (i.e.,
with thumbnails and a lightbox or carousel). Galleries use the `gallery.html`
template.

**NOTE**: containing index file, one or more directories (regardless of their
type), or any files that are not images disqualifies a directory from being of
type **GALLERY**. The directory **must** contain only images.

### Directories

- Directory: **yes**
- Type: **DIRECTORY**
- Template: `directory.html`

A directory with mixed content but no index file is of type **DIRECTORY**.
Typically, a simple file listing is automatically added to **DIRECTORY** nodes.
These use the `directory.html` template.

**NOTE**: containing an index file means the directory is a page bundle, *not*
a directory.

### Empty Directories

- Directory: **yes**
- Type: n/a
- Template: n/a

An empty directory is always ignored, not given a type, and generates nothing
in the target directory.


### Example Source Tree

```
site/                      <-- HOME
|-- index.md               <-- content for HOME (generates index.html)
|
|-- about/                 <-- PAGE BUNDLE (directory with an index file)
|   |-- index.md           <-- content for PAGE BUNDLE (generates about/index.html)
|   |-- photo.jpg
|
|-- colophon.md            <-- SINGLE PAGE (non-index file, generates colophon/index.html)
|
|-- empty/                 <-- empty directories are ignored
|
|-- archive/               <-- DIRECTORY (directory, no index, mixture of files and directories)
|   |-- article1.pdf       <-- STATIC FILE (copied to archive/article1.pdf)
|   |-- article2.md        <-- SINGLE PAGE (generates archive/article2/index.html)
|   |-- article3.html      <-- SINGLE PAGE (copied to archive/article3/index.html without processing)
|   |-- figure1.gif        <-- IMAGE (generates archive/figure1/index.html and copied to archive/figure1/figure1.gif)
|   |-- img/               <-- GALLERY (for now) but it would probably be nice to ignore this, somehow
|       |-- figure2.jpg    <-- IMAGE (generates archive/img/figure2/index.html and copied to archive/img/figure2/figure2.gif)
|
|-- photos/                <-- DIRECTORY (directory, no index, contains other directories, photos/index.html autogenerated)
|   |
|   |-- home/              <-- GALLERY (directory, no index, only images)
|   |   |-- portrait.jpg
|   |   |-- garden.jpg
|   |
|   |-- travel/            <-- PAGE BUNDLE (directory with index and images)
|       |-- index.md       <-- content for the PAGE BUNDLE (no automatic gallery insertion)
|       |-- photo1.jpg
|       |-- photo2.jpg
|       |-- photo3.jpg
|
|-- news/                  <-- DIRECTORY (directory, no index, text content)
|   |-- post1.md           <-- SINGLE PAGE (generates news/post1/index.html)
|   |-- post2.md           <-- SINGLE PAGE (generates news/post2/index.html)
|
|-- favicon.ico            <-- STATIC FILE (copied to favicon.ico)
```

## Image Metadata

### Raw Metadata

#### File Metadata

Assuming the image file is at `path`, and the `pyexif2` data is instantiated
with `img = pyexiv2.Image(str(path))`:

| property    | source                             |
|-------------|------------------------------------|
| file.name   |  basename, no extension            |
| file.type   |  MIME type, derived from extension |
| file.width  |  img.get_pixel_width()             |
| file.height |  img.get_pixel_height()            |
| file.mtime  |  os.stat(path).st_mtime            |
| file.ctime  |  os.stat(path).st_ctime            |

#### EXIF Metadata

| property             | source                                                  |
|----------------------|---------------------------------------------------------|
| exif.description     | Exif.Image.ImageDescription                             |
| exif.artist          | Exif.Image.Artist                                       |
| exif.datetime        | Exif.Photo.DateTimeOriginal                             |
| exif.copyright       | Exif.Image.Copyright                                    |
| exif.shutter_speed   | Exif.Photo.ShutterSpeedValue OR Exif.Photo.ExposureTime |
| exif.aperture        | Exif.Photo.ApertureValue OR Exif.Photo.FNumber          |
| exif.iso             | Exif.Photo.ISOSpeedRatings                              |
| exif.focal_length    | Exif.Photo.FocalLength                                  |
| exif.focal_length_35 | Exif.Photo.FocalLengthIn35mmFilm                        |
| exif.camera          | Exif.Image.Model                                        |
| exif.camera_make     | Exif.Image.Make                                         |
| exif.lens_info       | Exif.Photo.LensSpecification                            |
| exif.lens            | Exif.Photo.LensModel                                    |
| exif.lens_make       | Exif.Photo.LensMake                                     |
| exif.latitude        | Exif.GPSInfo.GPSLatitude                                |
| exif.latitude_ref    | Exif.GPSInfo.GPSLatitudeRef                             |
| exif.longitude       | Exif.GPSInfo.GPSLongitude                               |
| exif.longitude_ref   | Exif.GPSInfo.GPSLongitudeRef                            |

#### IPTC Metadata

| property             | source                          |
|----------------------|---------------------------------|
| iptc.name            | Iptc.Application2.ObjectName    |
| iptc.caption         | Iptc.Application2.Caption       |
| iptc.byline          | Iptc.Application2.Byline        |
| iptc.date            | Iptc.Application2.DateCreated   |
| iptc.time            | Iptc.Application2.TimeCreated   |
| iptc.copyright       | Iptc.Application2.Copyright     |
| iptc.country_code    | Iptc.Application2.CountryCode   |
| iptc.country         | Iptc.Application2.CountryName   |
| iptc.province_state  | Iptc.Application2.ProvinceState |
| iptc.city            | Iptc.Application2.City          |
| iptc.sublocation     | Iptc.Application2.SubLocation   |
| iptc.keywords        | Iptc.Application2.Keywords      |

#### XMP Metadata

| property      | source                           |
|---------------|----------------------------------|
| xmp.alt_text  | Xmp.iptcExt.AltTextAccessibility |
| xmp.subject   | Xmp.dc.subject                   |
| xmp.rating    | Xmp.xmp.Rating                   |

### Derived / Composite Metadata

These metadata properties will be direct properties of the image node. They
will be sourced from the above metadata (not via `pyexif2` directly).

| property       | source                                                            |
|----------------|-------------------------------------------------------------------|
| title          | iptc.name OR file.name                                            |
| description    | exif.description OR iptc.caption OR `None`                        |
| alt_text       | xmp_alt_text OR description OR title                              |
| artist         | exif.artist OR iptc.byline OR `None`                              |
| copyright      | exif.copyright OR iptc.copyright OR `None`                        |
| datetime       | exif.datetime OR iptc.date + iptc.time OR file.ctime              |
| camera         | exif.camera OR `None`                                             |
| lens           | exif.lens OR `None`                                               |
| exposure       | exif.shutter_speed, exif.aperture, exif.iso, exif.focal_length_35 |
| country        | iptc.country OR `None`                                            |
| province_state | iptc.province_state OR `None`                                     |
| state          | iptc.province_state                                               |
| province       | iptc.province_state                                               |
| city           | iptc.city OR `None`                                               |
| sublocation    | iptc.sublocation OR `None`                                        |
| location       | iptc.sublocation, iptc.city, iptc.province_state, iptc.country    |
| latitude       | exif.latitude + exif_latitude_ref OR `None`                       |
| longitude      | exif.longitude + exif_longitude_ref OR `None`                     |
| keywords       | iptc.keywords OR xmp.subject OR `[]`                              |
| rating         | xmp.rating OR `0`                                                 |
