# Segment nuclei with a BiaPy model, then a watershed you can tune (biapy-ops).
#
# Two ops in a row. predict.bmz runs the model and returns its raw channels --
# for resourceful-otter, F (foreground) and C (contours) -- and
# segment.watershed_by_channels turns them into labels. Run it again with
# other thresholds: the model is kept warm, so only the watershed is slow
# the first time.
#@ ImagePlus imp
#@ String (label = "Model", value = "resourceful-otter") model
#@ String (label = "Channels the model predicts", value = "F,C") channels
#@ String (label = "Seed thresholds (F, C), or auto", value = "auto,auto") seedThresholds
#@ String (label = "Growth mask threshold (F), or auto", value = "auto") growthThreshold
#@ Integer (label = "Smallest seed (pixels, 0 = keep all)", value = 0) minSeedSize
#@ Boolean (label = "Show the model's channels", value = false) showChannels
#@ UIService ui

from ij import IJ
from java.lang import System
from net.imagej.axis import Axes
from net.imglib2.img.display.imagej import ImageJFunctions
from net.imglib2.roi.labeling import LabelRegions
from net.imglib2.view import Views
from fiji_skopkit import skop

start = System.currentTimeMillis()

predicted = skop.biapy_ops.predict.bmz(imp, model=model, output="raw")

# Name the result's axes. An op can't yet declare its output's axes (opspec's
# OutputSpec has none), so Fiji names them after the input's, (x, y), and the
# third, the model's channels, lands first, as "X". A 2D model's raw output
# is (y, x, channel) in numpy order: (channel, x, y) here.
# TODO: drop this once ops can declare output axes.
if predicted.numDimensions() == 3:
  for d, axis in enumerate([Axes.CHANNEL, Axes.X, Axes.Y]):
    predicted.axis(d).setType(axis)

if showChannels and predicted.numDimensions() == 3:
  # Fiji shows x and y first: (channel, x, y) -> (x, y, channel), as a stack.
  view = Views.permute(Views.permute(predicted, 0, 1), 1, 2)
  shown = ImageJFunctions.wrap(view, "%s channels (%s)" % (imp.getShortTitle(), channels)).duplicate()
  shown.setTitle("%s channels (%s)" % (imp.getShortTitle(), channels))
  shown.show()

labels = skop.biapy_ops.segment.watershed_by_channels(
  predicted,
  channels=channels,
  seed_channels=channels,
  seed_thresholds=seedThresholds,
  growth_mask_channels=channels.split(",")[0],
  growth_mask_thresholds=growthThreshold,
  topographic_surface=channels.split(",")[0],
  min_seed_size=minSeedSize,
)

# An ImgLabeling, as a labels image: one colour per nucleus.
count = len(LabelRegions(labels).getExistingLabels())
out = ImageJFunctions.wrap(labels.getIndexImg(), "%s nuclei" % imp.getShortTitle()).duplicate()
out.setTitle("%s nuclei (%d)" % (imp.getShortTitle(), count))
IJ.run(out, "glasbey_on_dark", "")
IJ.resetMinAndMax(out)
out.show()

IJ.log("Nuclei: %d, %d ms" % (count, System.currentTimeMillis() - start))
