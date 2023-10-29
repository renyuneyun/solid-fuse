# SoLiD FUSE
- - - - - -

SolidFUSE is a FUSE (Filesystem in User Space) implementation to read/write to your [Solid (Social Linked Data) Pods](https://solidproject.org/).  
It aims to provide an easier way to manipulate resources in your Solid Pods and/or integrate some system tools with it.

> SolidFUSE does **not** really handle Linked Data, and SolidFUSE is **not** a replacement for Solid Apps. It merely takes advantage of the directory-like structure of resources stored in Solid Pods. To utilize the full power of Solid, you should use Solid Apps, which can make use of the *social* and *linked data* aspects of Solid.

This application is in its early stage. See Features / TODOs below. PRs are welcome.

## Usage

If you are new here, the following steps need to be performed (see explanation below):

1. Install dependencies
2. Create configuration file
3. Run application

### Install dependencies

We use `poetry` to manage environment and dependencies. You need to install it in accordance to your distro.  
After having it, run the following command to automatically create environment and install dependencies:

```
poetry install
```

### Configuration file

There is an example configuration file `config_example.toml` with the source. You should (make a copy and) modify it according to your credentials.

> I would recommend to copy it to `config.toml`, which is ignore by git as specified in `.gitignore`, in case you want to do some commits

### Run application

Assume your configuration file is named `config.toml`, and you want to mount it under `/mnt/solid`, run the following command:

```
poetry run src/solid-fuse.py config.toml /mnt/solid
```

## Note

This project is in early-stage. Breaking changes may be expected with every update.

SolidFUSE use [`solid-file-python`](https://github.com/twonote/solid-file-python) for authentication and performing operations. Currently, we use a [custom implementation](https://github.com/renyuneyun/solid-file-python) that integrated [solid-oidc-client](https://pypi.org/project/solid-oidc-client/) to support any Solid server (NSS, CSS, ESS). This will be changed after upstream has made the support official (see [this issue](https://github.com/twonote/solid-file-python/pull/33)).

## Features / TODOs

### Core functionality

- [x] Mount Solid Pod as a filesystem
- [x] Present the directory structure
- [x] Show file sizes
    - [ ] More efficient method (that does not require downloading the whole file)
- [x] Read file contents
    - [x] Text files
    - [x] Binary files
- [ ] Update cache
    - [ ] Automatically update cache after modification
    - [ ] Automatically update cache by time-out
- [x] Edit files
- [x] Create files
    - [ ] Update local cache after combined writing (e.g. after `echo 1 > file.txt`, but not after `touch file.txt`)
- [ ] Delete files
- [ ] Show linked files
    - [ ] ACL
    - [ ] Meta
- [ ] Show time

Note: creating linked files is impossible for a filesystem, because this notion does not exist.

### Authentication and Authorization

- [x] Log-in / Authenticate
- [ ] No-log-in support (public resources)
- [ ] Map (current user) permission as POSIX permission (no `chmod` support)
- [x] Change backend to support Solid servers other than NSS
    - [ ] Refresh token after expiration (an [upstream issue](https://pypi.org/project/solid-oidc-client/))

### Performance

- [x] Local (in-memory) caching
- [x] On-demand caching (do not download everything in the beginning)
- [ ] Cache expiration
- [ ] Really async and lock
    - [ ] File size async
    - [ ] Async with lock

### Misc features

- [x] Configuration file
- [ ] Command-line arguments
- [ ] Multiple Pods
- [x] Unmount when stopped

### Development

- [ ] Packaging
- [ ] Extract high-level interfaces for wrapping low-level FUSE interfaces
    - [ ] Maybe release as a separate library?

## License

Copyright 2023 Rui Zhao (renyuneyun)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
