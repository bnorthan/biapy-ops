# Run a BioImage Model Zoo model with BiaPy (biapy-ops), on the open image.
#
# The result opens as a new image: instance labels for an instance
# segmentation model, the restored image for a denoising or super-resolution
# one. The first run builds BiaPy's environment (several GB) and downloads the
# model; later runs reuse both.
#@ ImagePlus imp
#@ String (label = "Model (BioImage Model Zoo id or nickname)", value = "resourceful-otter") model
#@ String (label = "Output", choices = {"final", "raw"}, description = "final: BiaPy's end result. raw: the network's channels, before post-processing.") output
#@ Boolean (label = "Use the GPU if there is one", value = true) useGpu
#@ UIService ui

from ij import IJ
from java.lang import System
from fiji_skopkit import skop

start = System.currentTimeMillis()

result = skop.biapy_ops.predict.bmz(imp, model=model, output=output, use_gpu=useGpu)

title = "%s (%s, %s)" % (imp.getShortTitle(), model, output)
ui.show(title, result)
shown = IJ.getImage()
if output == "final" and shown.getBitDepth() != 24:
  IJ.run(shown, "glasbey_on_dark", "")  # labels: one colour per object
IJ.resetMinAndMax(shown)

IJ.log("%s: %s, %d ms" % (model, title, System.currentTimeMillis() - start))
