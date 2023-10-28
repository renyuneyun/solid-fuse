import stat
import os
import errno
import pyfuse3
import logging

import urllib.parse
from pathlib import PurePath

import mimetypes

from solid.auth import Auth
from solid.solid_api import SolidAPI

from solid.solid_api import FolderData


log = logging.getLogger(__name__)


# @dataclass
# class MyFolderInfo:


class InternalMappingNotFoundException(Exception):
    pass

class LocalInfoNotFoundException(Exception):
    pass


class UriWrapper:
    def __init__(self, uri):
        self.uri = uri

    def is_container(self):
        return self.uri.endswith('/')

    def parent(self):
        rep = urllib.parse.urlparse(self.uri)
        rep = rep._replace(path=str(PurePath(rep.path).parent / '/'))  # FIXME: Error, property cannot be edited
        return UriWrapper(urllib.parse.urlunparse(rep))

    def child(self, child_path):
        child_path = child_path.decode()
        rep = urllib.parse.urlparse(self.uri)
        rep = rep._replace(path=str(PurePath(rep.path) / child_path))
        return UriWrapper(urllib.parse.urlunparse(rep))

    def __str__(self):
        return self.uri


class ResourceInfoCache:
    '''
    A helper class that caches Solid resource information
    '''
    def __init__(self):
        self._cache = {}

    def has(self, uri):
        return uri in self._cache

    def put(self, uri, info):
        self._cache[uri] = info

    def get(self, uri):
        return self._cache[uri]

    def delete(self, uri):
        del self._cache[uri]


class ResourceLinkHelper:
    '''
    A helper class that handles information related to conversion / linking
    between inodes, fd, and Solid URIs
    '''

    def __init__(self):
        self.inode_count = pyfuse3.ROOT_INODE
        self._uri_map = {}
        self._file_handler_map = {}
        # self.insert_resource(root_uri, root_inode)

    def new_inode(self):
        # TODO: Add lock
        self.inode_count += 1
        return self.inode_count

    def set_fh(self, inode):
        self._file_handler_map[inode] = inode

    def fh(self, inode):
        if inode not in self._file_handler_map:
            self.set_fh(inode)
        return self._file_handler_map[inode]

    def insert(self, uri, inode=None):
        if inode is None:
            inode = self.new_inode()
        fh = self.fh(inode)
        self._uri_map[fh] = uri

    def get_uri_from_inode(self, inode):
        return self._uri_map[self.fh(inode)]

    def get_uri_from_fh(self, fh):
        return self._uri_map[fh]

    def get_inode_from_uri(self, uri):
        for k, v in self._uri_map.items():
            if v == uri:
                for k2, v2 in self._file_handler_map.items():
                    if v2 == k:
                        return k2
        raise InternalMappingNotFoundException()

    def has_inode(self, inode):
        return inode in self._file_handler_map


class ResourceInfoLinkWrapper:
    def __init__(self, pod, idp, username, password):
        auth = Auth()
        self._api = SolidAPI(auth)
        auth.login(idp, username, password)
        self._resource_link_helper = ResourceLinkHelper()
        self._container_info_cache = ResourceInfoCache()
        self._resource_info_cache = ResourceInfoCache()
        self._resource_contant_cache = ResourceInfoCache()

        self._resource_link_helper.insert(pod, pyfuse3.ROOT_INODE)
        self.retrieve_and_cache(pod)  # Initialization needs optimization

    def retrieve_and_cache(self, uri, is_container=True):
        log.debug(f"retrieve_and_cache({uri})")
        folder_info = self._api.read_folder(uri)
        self._container_info_cache.put(uri, folder_info)
        for sub in folder_info.folders:
            log.debug(f"Sub-dir-info type: {sub.itemType}, of {sub.url}")
            self._resource_link_helper.insert(sub.url)
            self._resource_info_cache.put(sub.url, sub)

        for sub in folder_info.files:
            log.debug(f"Sub-res-info type: {sub.itemType}, of {sub.url}")
            inode = self._resource_link_helper.new_inode()
            self._resource_link_helper.insert(sub.url, inode)
            self._resource_info_cache.put(sub.url, sub)
            self.retrieve_and_cache_resource(sub.url)

    def retrieve_and_cache_resource(self, uri):
        log.debug(f"retrieve_and_cache_resource({uri})")
        response = self._api.get(uri)
        # TODO: Handle binary data
        # data = response.read()
        # self._resource_contant_cache.put(uri, data)
        data = response.read()
        self._resource_contant_cache.put(uri, data)

    def prepare(self, inode=None, fh=None, uri=None):
        log.debug(f"prepare({inode}, {fh}, {uri})")
        self.get(inode, fh, uri)
        return self._resource_link_helper.fh(inode)

    def prepare_resource(self, inode=None, fh=None, uri=None):
        log.debug(f"prepare_resource({inode}, {fh}, {uri})")
        self.get_resource(inode, fh, uri)
        return self._resource_link_helper.fh(inode)

    def get(self, inode=None, fh=None, uri=None, from_info_cache=True):
        if inode:
            fh = self._resource_link_helper.fh(inode)
        if fh:
            uri = self._resource_link_helper.get_uri_from_fh(fh)
        if from_info_cache:
            if inode == pyfuse3.ROOT_INODE:
                return self._container_info_cache.get(uri)
            if self._resource_info_cache.has(uri):
                info = self._resource_info_cache.get(uri)
                return info
            raise LocalInfoNotFoundException()
            
        if not self._container_info_cache.has(uri):
            if UriWrapper(uri).is_container():
                self.retrieve_and_cache(uri)
            else:
                uri_p = UriWrapper(uri).parent().uri
                self.retrieve_and_cache(uri_p)
                # TODO: Handle potential error when uri is not a subpath of SOLID_POD
        return self._container_info_cache.get(uri)

    def get_resource(self, inode=None, fh=None, uri=None):
        if inode:
            fh = self._resource_link_helper.fh(inode)
        if fh:
            uri = self._resource_link_helper.get_uri_from_fh(fh)
        if not self._resource_contant_cache.has(uri):
            self.retrieve_and_cache_resource(uri)
        content = self._resource_contant_cache.get(uri)
        return content

    def get_inode(self, uri):
        return self._resource_link_helper.get_inode_from_uri(uri)

    def gen_inode_for_uri(self, uri):
        inode = self._resource_link_helper.new_inode()
        self._resource_link_helper.insert(uri, inode)
        return inode

    def has_inode(self, inode):
        return self._resource_link_helper.has_inode(inode)

    def size_of_resource(self, inode=None, fh=None, uri=None):
        content = self.get_resource(inode, fh, uri)
        return len(content)

    def put_resource(self, data, inode=None, fh=None, uri=None):
        if inode:
            fh = self._resource_link_helper.fh(inode)
        if fh:
            uri = self._resource_link_helper.get_uri_from_fh(fh)
        mtype, encoding = mimetypes.guess_type(uri)
        self._api.put_file(uri, data, mtype)


class SolidFs(pyfuse3.Operations):
    def __init__(self, pod, idp=None, username=None, password=None):
        super(SolidFs, self).__init__()
        self._resource_info_link_wrapper = ResourceInfoLinkWrapper(
            pod, idp, username, password)

    async def getattr(self, inode, ctx=None):
        log.debug(f"getattr({inode}, {ctx})")
        entry = pyfuse3.EntryAttributes()
        # if inode == pyfuse3.ROOT_INODE:
        #     entry.st_mode = (stat.S_IFDIR | 0o755)
        #     entry.st_size = 0
        # else:
        info = self._resource_info_link_wrapper.get(inode, from_info_cache=True)
        if UriWrapper(info.url).is_container():
            entry.st_mode = (stat.S_IFDIR | 0o755)
            entry.st_size = 0
        else:
            entry.st_mode = (stat.S_IFREG | 0o644)
            entry.st_size = self._resource_info_link_wrapper.size_of_resource(inode)

        stamp = int(1438467123.985654 * 1e9)
        entry.st_atime_ns = stamp
        entry.st_ctime_ns = stamp
        entry.st_mtime_ns = stamp
        entry.st_gid = os.getgid()
        entry.st_uid = os.getuid()
        entry.st_ino = inode

        return entry

    async def lookup(self, parent_inode, name, ctx=None):
        log.debug(f"lookup({parent_inode}, {name}, {ctx})")
        if name == '.':
            return await self.getattr(parent_inode)
        if name == '..':
            folder_data = self._resource_info_link_wrapper.get(parent_inode, from_info_cache=True)
            parent_url = UriWrapper(folder_data.url).parent().uri
            try:
                parent_inode = self._resource_info_link_wrapper.get_inode(parent_url)
                return await self.getattr(parent_inode)
            except InternalMappingNotFoundException:
                raise pyfuse3.FUSEError(errno.ENOENT)
        parent_folder_data = self._resource_info_link_wrapper.get(parent_inode, from_info_cache=True)
        target_url = UriWrapper(parent_folder_data.url).child(name).uri
        try:
            target_inode = self._resource_info_link_wrapper.get_inode(target_url)
            return await self.getattr(target_inode)
        except InternalMappingNotFoundException:
            raise pyfuse3.FUSEError(errno.ENOENT)

    async def opendir(self, inode, ctx):
        log.debug(f"opendir({inode}, {ctx})")
        if not self._resource_info_link_wrapper.has_inode(inode):
            raise pyfuse3.FUSEError(errno.ENOENT)
        fh = self._resource_info_link_wrapper.prepare(inode)
        return fh

    async def readdir(self, fh, start_id, token):
        log.debug(f"readdir({fh}, {start_id}, {token})")
        folder_data = self._resource_info_link_wrapper.get(fh=fh, from_info_cache=False)
        if start_id < len(folder_data.folders) + len(folder_data.files):
            for i, sub_data in enumerate(folder_data.folders):
                if start_id and i < start_id: continue
                sub_inode = self._resource_info_link_wrapper.gen_inode_for_uri(sub_data.url)
                pyfuse3.readdir_reply(token, sub_data.name.encode(), await self.getattr(sub_inode), i+1)
            for i, sub_data in enumerate(folder_data.files, len(folder_data.folders)):
                if start_id and i < start_id: continue
                sub_inode = self._resource_info_link_wrapper.gen_inode_for_uri(sub_data.url)
                pyfuse3.readdir_reply(token, sub_data.name.encode(), await self.getattr(sub_inode), i+1)
        return

    # async def setxattr(self, inode, name, value, ctx):
    #     if inode != pyfuse3.ROOT_INODE or name != b'command':
    #         raise pyfuse3.FUSEError(errno.ENOTSUP)

    #     if value == b'terminate':
    #         pyfuse3.terminate()
    #     else:
    #         raise pyfuse3.FUSEError(errno.EINVAL)

    async def open(self, inode, flags, ctx):
        log.debug(f"open({inode}, {flags:b}, {ctx})")
        if not self._resource_info_link_wrapper.has_inode(inode):
            raise pyfuse3.FUSEError(errno.ENOENT)
        # if flags & os.O_RDWR or flags & os.O_WRONLY:
        #     raise pyfuse3.FUSEError(errno.EACCES)
        fh = self._resource_info_link_wrapper.prepare_resource(inode)
        return pyfuse3.FileInfo(fh=fh)

    async def read(self, fh, off, size):
        log.debug(f"read({fh}, {off}, {size})")
        data = self._resource_info_link_wrapper.get_resource(fh=fh)
        return data[off:off+size]

    async def access(self, inode, mode, ctx):
        log.debug(f"access({inode}, {mode}, {ctx})")
        return True

    async def write(self, fh, offset, buf):
        log.debug(f"write({fh}, {offset}, {buf})")
        # try:
        data = self._resource_info_link_wrapper.get_resource(fh=fh)
        # except InternalMappingNotFoundException:
        #     data = b''

        data = data[:offset] + buf + data[offset+len(buf):]

        self._resource_info_link_wrapper.put_resource(data, fh=fh)

        return len(buf)
