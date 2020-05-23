import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def del_all(targetDir):
    os.chdir(targetDir)
    files = os.listdir()
    for file in files:
        os.remove(targetDir + '/' + file)
    return

def create_file(filename,size):
    # size in GiB
    with open(filename, "wb") as out:
        out.seek((size*1024 * 1024 * 1024) - 1)
        out.write(b'\0')

def house_keeping(targetDir,targetSpace,match_str):
    # targetSpace in GiB
    #
    os.chdir(targetDir)
    files_ = os.listdir()
    files = sorted([file for file in files_ if match_str in file])
    nfiles = len(files)
    # for file in files:
    #     logger.debug(file)
    logger.info('nfiles={}'.format(nfiles))
    cur = 0
    # logger.info('Before: Free = {:.1f}GiB, Target={:.1f}GiB'.format(os.getfree(targetDir)/(1024*1024),targetSpace))
    while os.getfree(targetDir) < targetSpace*1024*1024:
        if match_str in files[cur]:
            os.remove(targetDir + '/' + files[cur])
            logger.info('{} deleted.'.format(files[cur]))
        cur += 1
        if cur == nfiles:
            logger.error('no matching file found!')
    # logger.info('After : Free = {}GiB, Target={}GiB'.format(os.getfree(targetDir)/(1024*1024),targetSpace))
    return
