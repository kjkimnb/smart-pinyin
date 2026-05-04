"""遥操作论文复现包.

复现 Chen et al. (2018) "An Improved Wave-Variable Based Four-Channel
Control Design in Bilateral Teleoperation System for Time-Delay Compensation",
IEEE Access, DOI 10.1109/ACCESS.2018.2805782.
"""

from .master import Master, MasterParams
from .slave import Slave, SlaveParams

__all__ = ["Master", "MasterParams", "Slave", "SlaveParams"]
