import xbmc, xbmcgui, shutil, urllib2, urllib, os, xbmcaddon, zipfile, time

addon = xbmcaddon.Addon('plugin.program.podgodwizard')
url        = 'https://archive.org/download/podgod/backup.zip'
path       = xbmc.translatePath('special://home/addons/packages')
lib        = xbmc.translatePath(os.path.join(path,'backup.zip'))
home       = xbmc.translatePath('special://home')
profile    = 'Master user'
lock       = 'false'
localtxt00 = 'PGTV'
localtxt01 = 'Install'
localtxt02 = 'Downloading Latest PGTV Version. Please Wait.'
localtxt03 = 'Downloaded: '
localtxt04 = 'Download Cancelled.'
localtxt05 = 'Updating'
localtxt06 = 'Succeeded'
localtxt07 = 'Unpacking PGTV.zip. Please Wait.'

def DownloaderClass(url,dest):
        dp = xbmcgui.DialogProgress()
        dp.create(localtxt00,localtxt02,'')
        urllib.urlretrieve(url,dest,lambda nb, bs, fs, url=url: _pbhook(nb,bs,fs,url,dp))

def _pbhook(numblocks, blocksize, filesize, url=None,dp=None):
        try:
                percent = min((numblocks*blocksize*100)/filesize, 100)
                print localtxt03+str(percent)+'%'
                dp.update(percent)
        except:
                percent = 100
                dp.update(percent)
        if dp.iscanceled():
                raise Exception("Cancelled")
                dp.close()

def ExtractorClass(_in, _out):
        dp = xbmcgui.DialogProgress()
        dp.create(localtxt00,localtxt07,'')
        zin    = zipfile.ZipFile(_in,  'r')
        nFiles = float(len(zin.infolist()))
        count  = 0
        for item in zin.infolist():
                count += 1
                update = count / nFiles * 100
                zin.extract(item, _out)

if __name__ == '__main__':
        dialog = xbmcgui.Dialog()
        try:
                DownloaderClass(url,lib)
        except:
                xbmc.executebuiltin('Notification(Download Failed,Please Try Again Later,50000,special://skin/icon.png)')
        time.sleep(1)
        try:
                ExtractorClass(lib,home)
        except:
                xbmc.executebuiltin('Notification(Unpacking Failed,Please Try Again Later,50000,special://skin/icon.png)')
        time.sleep(1)
        xbmc.executebuiltin('UpdateLocalAddons')
        xbmc.executebuiltin('UpdateAddonRepos')
        xbmc.executebuiltin('RunScript(service.installer)')

