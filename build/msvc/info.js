buildInfo.env = (function() {
    var sh = new BuildHelper.BourneShellNotationReader();
    WScript.Echo(buildInfo.projectDir + '\\ecell_version.sh');
    sh.eval(FileSystemObject.GetFile(
            buildInfo.projectDir + '\\ecell_version.sh'));
    
    return sh.env.mix({
        top_srcdir: buildInfo.projectDir + '\\ecell',
        bindir: '${prefix}/bin',
        libdir: '${prefix}/lib',
        datadir: '${prefix}/share/ecell',
        confdir: '${prefix}/etc',
        ECELL_DIRNAME: 'ecell-'
            + sh.env.ECELL_MAJOR_VERSION + '.' + sh.env.ECELL_MINOR_VERSION,
        ECELL_VERSION_STRING: '"' + sh.env.ECELL_VERSION_NUMBER + '"',
        VERSION: sh.env.ECELL_VERSION_NUMBER,
        INCLTDL: '/I' + buildInfo.projectDir + '\\libltdl',
        DMTOOL_INCLUDE_DIR: buildInfo.projectDir,
        NUMPY_INCLUDE_DIR: buildInfo.pythonHome + '\\lib\\site-packages\\numpy\\core\\include',
        LTDL_SHLIB_EXT: '.dll',
        CXXFLAGS: '',
        CPPFLAGS: '-DBOOST_ALL_NO_LIB=1 -DWIN32=1 -D_WIN32=1 -D__STDC__=1 -D_WIN32_WINNT=0x500 -D_SECURE_SCL=0',
        LDFLAGS: ''
    });
})();

buildInfo.productInfo = {
	name: 'E-Cell',
	shortName: 'ecell',
    version: {
        major: buildInfo.env.ECELL_MAJOR_VERSION,
        minor: buildInfo.env.ECELL_MINOR_VERSION,
        micro: buildInfo.env.ECELL_MICRO_VERSION,
        revision: buildInfo.env.ECELL_PACKAGE_REVISION
    }
};
