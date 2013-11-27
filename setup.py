import distutils.sysconfig
from distutils.core import setup
from distutils import cmd
from distutils.command.install_data import install_data as _install_data
from distutils.command.build import build as _build
import os
import glob

import palisades
import palisades.i18n.msgfmt

SITE_PACKAGES = distutils.sysconfig.get_python_lib()

class build_translations(cmd.Command):
    description = 'Compile .po files to .mo files'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        po_dir = os.path.join(os.path.dirname(os.curdir), 'po')
        for path, names, filenames in os.walk(po_dir):
            for filepath in filenames:
                if filepath.endswith('.po'):
                    lang_code = filepath[:-3]
                    src = os.path.join(path, filepath)
                    dest_path = os.path.join('build', 'locale', lang_code,
                            'LC_MESSAGES')
                    dest = os.path.join(dest_path, 'palisades.mo')
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)

                    # I always want to recompile.
                    print 'Compiling %s to %s' % (src, dest)
                    palisades.i18n.msgfmt.make(src, dest)

class build(_build):
    sub_commands = _build.sub_commands + [('build_trans', None)]
    def run(self):
        _build.run(self)

class install_data(_install_data):
    def run(self):
        for lang in os.listdir('build/locale'):
            lang_dir = os.path.join(SITE_PACKAGES, 'palisades', 'i18n',
                'locale', lang, 'LC_MESSAGES')
            lang_file = os.path.join('build', 'locale', lang, 'LC_MESSAGES',
                'palisades.mo')
            self.data_files.append((lang_dir, [lang_file]))
        _install_data.run(self)

icon_dir = os.path.join(SITE_PACKAGES, 'palisades', 'gui', 'icons')
data_files = [(icon_dir, glob.glob('palisades/gui/icons/*.png'))]

setup(
    name      = 'palisades',
    version   = palisades.__version__,
    packages  = ['palisades', 'palisades.gui', 'palisades.i18n'],
    license   = 'Apache',
    data_files = data_files,
    cmdclass  = {
        'build': build,
        'build_trans': build_translations,
        'install_data': install_data},
)
