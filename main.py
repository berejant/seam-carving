#!/usr/bin/env python3

import sys, getopt
import cv2
from SeamCarving import SeamCarving
from SeamCarvingNonOpt import SeamCarvingNonOpt
from SeamCarvingWithMask import SeamCarvingWithMask

if __name__ == "__main__":
    cmd_template = sys.argv[0] + " --crop <pixel_for_crop> --silent <input_file> [<output_file>]" \
                                 " --crop -c [OPTIONAL, default 100] pixel count for crop" \
                                 " --silent -s flag Disable render step-by-step on display" \
                                 " --non-opt -O boolean flag use non optimized realization" \
                                 "<input_file> path source" \
                                 "<output_file> path for save result"

    try:
        shortopts = "hsc:m:O"
        longopt = ["help", "silent", "crop=", "mask=", "non-opt"]
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopt)
        opts.extend(getopt.getopt(args[2:], shortopts, longopt)[0])
        if not args:
            raise getopt.GetoptError('<input_file> is require')
    except getopt.GetoptError as e:
        print(e)
        print(cmd_template)
        sys.exit(-2)

    input = args[0]
    output = args[1] if len(args) >= 2 else None
    silent = False
    crop = 100
    use_opt = True
    mask = None
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(cmd_template)
            sys.exit(-1)
        elif opt in ("-c", "--crop"):
            crop = int(arg)
        elif opt in ("-s", "--silent"):
            silent = True
        elif opt in ("-O", "--non-opt"):
            use_opt = False
        elif opt in ("-m", "--mask"):
            mask = arg

    if crop < 1:
        print("Bad crop size: " + str(crop))
        sys.exit(-1)

    if silent and not output:
        print("You can not run in Silent mode without output file")
        sys.exit(-1)

    image = cv2.imread(input) if isinstance(input, str) else None
    if image is None:
        print('Failed to read ' + input)
        sys.exit(-1)

    if mask is None:
        seamCarving = SeamCarving(image) if use_opt else SeamCarvingNonOpt(image)
    else:
        mask = cv2.imread(mask)
        seamCarving = SeamCarvingWithMask(image, mask)

    if silent:
        for i in range(crop):
            seam = seamCarving.find_seam()
            seamCarving.remove_seam(seam)

    else:
        window_name = 'Carving'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, seamCarving.image)
        cv2.waitKey(1)
        cv2.resizeWindow(winname=window_name, height=max(750, seamCarving.image.shape[0]),
                         width=max(1000, seamCarving.image.shape[1]))

        for i in range(crop):
            seam = seamCarving.find_seam()
            seamCarving.mark_seam_as_red(seam)
            cv2.imshow(window_name, seamCarving.image)
            cv2.waitKey(1)
            seamCarving.remove_seam(seam)

        cv2.imshow(window_name, seamCarving.image)
        cv2.imshow(window_name + '_original', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if output:
        cv2.imwrite(output, seamCarving.image)
