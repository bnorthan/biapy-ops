# Run by oprunner (and fiji-skopkit) at worker start-up, on the worker's main
# thread.
#
# Load the native libraries the ops need here, not inside an op. Appose runs
# each op call on a thread of its own, and on Windows a DLL loaded for the
# first time from such a thread can deadlock against the threads torch has
# already started. It did: watershed_by_channels hung forever, idle, loading
# scipy.interpolate's _fitpack extension (biapy post_processing ->
# scipy.signal -> scipy.interpolate). tnia-ops' photo environment hit the same
# thing in scipy.linalg.
#
# So import BiaPy itself, whole, here: every module the ops import, and with
# them every extension those modules load. It makes a worker's start-up a few
# seconds slower and every op call safe.
import torch  # noqa: F401
import scipy.linalg  # noqa: F401
import scipy.optimize  # noqa: F401
import scipy.signal  # noqa: F401
import scipy.interpolate  # noqa: F401
import biapy.data.post_processing.post_processing  # noqa: F401  (watershed_by_channels)
import biapy._biapy  # noqa: F401  (BiaPy, for predict.bmz: every workflow and model)
