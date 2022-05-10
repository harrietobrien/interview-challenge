"""
@author: Harriet O'Brien
"""
import shutil
import copy
import csv
import os


class ParseCSV:

    def __init__(self, csv_path, wd_path):
        self.csv = csv_path
        self.path = wd_path
        self.rows = self.csv_rows(self.csv)
        self.idd = self.id_dict(self.rows)
        self.folders = self.get_folders(self.idd)
        self.files = self.get_files(self.idd)
        self.root = self.get_root()
        self.rname = self.folders[self.root]['name']
        self.check_existence()
        assert(not os.path.exists(self.path + self.rname))
        self.id_paths = self.recreate_library()
        self.recreate_files()

    def check_existence(self):
        """
        :parameter: self (to retrieve wd path)
        :returns: None
        If root directory already exists,
        delete it for recreation
        """
        rname = self.rname
        if os.path.exists(self.path + rname):
            shutil.rmtree(self.path + rname)
            return
        else:
            assert(not os.path.isdir(self.path + rname))

    @staticmethod
    def csv_rows(filename):
        """
        csv_rows(filename)
        :parameter: CSV file (path)
        :returns: list of rows (str) retrieved from CSV
        """
        with open(filename, 'r', encoding='utf-8-sig') as csv:
            rows = list()
            for line in csv:
                rows.append(line.strip())
            return rows

    @staticmethod
    def id_dict(rows):
        """
        id_dict(rows)
        :parameter: list of rows (str)
        :returns: dict mapping IDs to their name, type, parent, & contents
        """
        data = dict()
        # skip label
        for i in range(1, len(rows)):
            r = rows[i]  # row string
            # split by comma excluding those within quotes 
            csv_objs = csv.reader([r], delimiter=',', quotechar='"')
            idl = list(csv_objs)[0]  # id list
            _id = idl[0]  # unique id
            # initialize dict at data[uid] using id as key
            data[_id] = dict()
            data[_id]['name'] = idl[1]
            data[_id]['type'] = idl[2]
            data[_id]['parent_id'] = idl[3]
            data[_id]['contents'] = idl[4]
        return data

    @staticmethod
    def get_folders(id_dict):
        """
        get_folders(id_dict)
        :parameter: dict mapping IDs to their info (id_dict(rows))
        :returns: dict mapping IDs of type 'folder' to their info
        """
        folders = dict()
        for k in id_dict:
            # type : folder
            if id_dict[k]['type'] == 'folder':
                folders[k] = id_dict[k]
        return folders

    @staticmethod
    def get_files(id_dict):
        """
        get_files(id_dict)
        :parameter: dict mapping IDs to their info (id_dict(rows))
        :returns: dict mapping IDs of type 'files' to their info
        """
        files = dict()
        for k in id_dict:
            # type : file
            if id_dict[k]['type'] == 'file':
                files[k] = id_dict[k]
        return files

    def find_set(self, d, k, v):
        """
        find_set(self, d, k, v)
        :parameter: dict, key, and value
        :returns: dict mapping each parent to list of children
        """
        for key, val in d.items():
            if key == '':
                self.find_set(d[key], k, v)
                return
            if key == k:
                d[key] = dict()
                for i in v:
                    d[key][i] = None
                return d
        d[k] = dict()
        for i in v:
            d[k][i] = None
        return d

    def family_tree(self, ftype):
        """
        family_tree(self, ftype)
        :parameter: str 'files' or 'folders'
        :returns: dict mapping each parent to list of children
        """
        if ftype == 'files':
            x = copy.deepcopy(self.files)
        elif ftype == 'folders':
            x = copy.deepcopy(self.folders)
        # get unique parent folders
        parents = list()
        for k in x:
            parent = x[k]['parent_id']
            if parent not in parents:
                parents.append(parent)
        tree = dict()
        for p in parents:
            for k in x:
                if p == x[k]['parent_id']:
                    # find parent id
                    if p not in tree:
                        tree[p] = [k]
                    else:
                        tmp = tree[p]
                        tmp.append(k)
                        tree[p] = tmp
        out = dict()
        for _id, lst in tree.items():
            self.find_set(out, _id, lst)
        return out

    def id_to_dir(self):
        """
        id_to_dir(self)
        :parameter: self (to retrieve folders)
        :returns: dict mapping ids to dir name
        """
        folders = copy.deepcopy(self.folders)
        out = dict()
        for f in folders:
            out[f] = folders[f]['name']
        return out

    def id_to_file(self):
        """
        id_to_file(self)
        :parameter: self (to retrieve files)
        :returns: dict mapping ids to file name
        """
        files = copy.deepcopy(self.files)
        out = dict()
        for f in files:
            out[f] = files[f]['name']
        return out

    def get_root(self):
        """
        get_root(self)
        :parameter: self (to retrieve folders)
        :returns: id (str) of the root directory
        """
        folders = copy.deepcopy(self.folders)
        for f in folders:
            if not folders[f]['parent_id']:
                return f

    def recreate_library(self):
        """
        recreate_library(self)
        :parameter: self (to retrieve fam tree, root, path)
        :returns: dict mapping each folder id to its path
        (to be called in recreate_files)
        Creates directories for all folders
        """
        n = self.id_to_dir()
        root = self.root
        cp = self.path + n[root]
        os.mkdir(cp)
        out = self.family_tree('folders')
        id_paths = dict()
        id_paths[root] = cp

        def recursive_helper(path, start=out[root]):
            for i in start:
                if i in out:
                    os.mkdir(path + '/' + n[i])
                    id_paths[i] = path + '/' + n[i]
                    recursive_helper(path + '/' + n[i], out[i])
                else:
                    os.mkdir(path + '/' + n[i])
                    id_paths[i] = path + '/' + n[i]

        recursive_helper(cp)
        return id_paths

    def recreate_files(self):
        """
        recreate_files(self)
        :parameter: self (to retrieve fam tree, root, path)
        :returns: None
        Creates text files with contents for all files
        """
        n = self.id_to_file()
        idp = self.id_paths

        for file in self.files:
            parent = self.files[file]['parent_id']
            ppath = idp[parent]
            name = n[file]
            x = os.path.join(ppath, name)
            f = open(x, 'w')
            content = self.files[file]['contents']
            f.write(content)
            f.close()

    def __str__(self):
        def format_dict(d, indent=0):
            for key, value in d.items():
                print('\t' * indent + str(key))
                if isinstance(value, dict):
                    format_dict(value, indent + 1)
                else:
                    print('\t' * (indent + 1) + str(value))

        files = self.family_tree('files')
        folders = self.family_tree('folders')
        format_dict(folders, indent=0)
        format_dict(files, indent=0)
        return


if __name__ == "__main__":
    pwd = os.getcwd() + '/'
    csv_file = pwd + 'export.csv'
    test = ParseCSV(csv_file, pwd)
