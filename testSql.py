
from itsmisc import ItsConfig
from itsdb import ItsSqlConnection
import imageio
import numpy as np

cfg = ItsConfig(ItsConfig.CONFIG_PATH)
con = ItsSqlConnection(cfg.sql_cfg)

classes = con.getBesIdsPerClasses()

for i in range(len(classes)):
    img = con.getImageFromRequestHistory(classes[i])
    img = (img * 255).round().astype(np.uint8)
    imageio.imwrite('{}.png'.format(i), img)
    