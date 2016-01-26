import os
import subprocess
import time
import shutil
#from sl_codebase.utils.file_utils import FileUtils
import sys
if not 'E:\\CODE_DEV\\' in sys.path:
    sys.path.append('E:\\CODE_DEV\\')
from rooftops.utils import global_settings as gs



class MovieMerge(object):

    def __init__(self, folder, watch=False):
        '''
        :param folder: the folder to operate on
        :param watch: whether or not to continuously watch the folder, False by default
        :return:
        '''
        self.folder = folder
        dirs = [os.path.join(self.folder, dir) for dir in os.listdir(self.folder) if os.path.isdir(os.path.join(self.folder, dir))]

        self.initial_state = {}
        for dir in dirs:
            for file in os.listdir(dir):
                if file.endswith(".mov") and not 'combined' in file:
                    mod = os.path.getmtime(os.path.join(dir, file))
                    if dir in self.initial_state.keys():
                        files = self.initial_state[dir]
                        files.append([file, mod])
                        self.initial_state[dir] = files
                    else:
                        self.initial_state[dir] = [[file, mod]]

        for dir, files in self.initial_state.iteritems():
            paths = []
            for item in files:
                paths.append(os.path.join(dir, item[0]))
            self.merge_movs(paths)

        if watch:
            self.__watch()

    def __watch(self):
        while 1:
            #print 'watching'
            time.sleep(5)
            for dir, dir_files in self.initial_state.iteritems():
                files = []

                for file in os.listdir(dir):
                    if file.endswith(".mov") and not 'combined' in file:
                        mod = os.path.getmtime(os.path.join(dir, file))
                        files.append([file, mod])
                added = []

                for item in files:
                    for file in dir_files:
                        if item[0] == file[0] and item[1] != file[1]:
                            added.append(item)

                if added or len(files) < len(dir_files) or len(files) > len(dir_files):
                    paths = []
                    for item in files:
                        paths.append(os.path.join(dir, item[0]))
                    self.merge_movs(paths)

                for add in added:
                    print "movie %s added" % add[0]

                self.initial_state[dir] = files

    def merge_movs(self, mov_paths):
        mov_paths.sort()
        folder_name = os.path.basename(os.path.dirname(mov_paths[0]))
        out = os.path.join(self.folder, "%s_combine.mov" % folder_name)
        out = out.replace("\\", "/")

        if len(mov_paths) == 1:
            shutil.copy(mov_paths[0], out)
            return

        cmd = "%s -y " % gs.globalSettings['ffmpeg']
        for item in mov_paths:
            item = item.replace("\\", "/")
            cmd += "-i %s " % item
        cmd += '-filter_complex "'

        count = 0
        for item in mov_paths:
            cmd += "[%d:0] [%d:1] " % (count, count)
            count += 1

        cmd += 'concat=n=%d:v=1:a=1 [v] [a]" -map "[v]" -map "[a]" %s' % (len(mov_paths), out)

        print '\n\n\n%s\n\n' % cmd

        try:
            subprocess.check_call(cmd)
            print "Combined file written to %s" % out
        except subprocess.CalledProcessError:
            print "Combine failed."

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Movie Combiner")
    parser.add_argument("folder", action="store", help="The folder to operate on.")
    parser.add_argument("-watch", dest="watch", action="store_true", help="Run in continuous watch mode.")

    result = parser.parse_args()

    if result.folder:
        if result.watch:
            MovieMerge(result.folder, watch=True)
        else:
            MovieMerge(result.folder)

