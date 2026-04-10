#!/usr/bin/env python

# Functions for ICA-AROMA v0.3 beta

from __future__ import division
from __future__ import print_function

import numpy as np


def runICA(fslDir, inFile, outDir, melDirIn, mask, dim, TR):
    """Run MELODIC and merge the thresholded IC maps."""
    import os
    import subprocess

    melDir = os.path.join(outDir, "melodic.ica")
    melIC = os.path.join(melDir, "melodic_IC.nii.gz")
    melICmix = os.path.join(melDir, "melodic_mix")
    melICthr = os.path.join(outDir, "melodic_IC_thr.nii.gz")

    if (
        len(melDirIn) != 0
        and os.path.isfile(os.path.join(melDirIn, "melodic_IC.nii.gz"))
        and os.path.isfile(os.path.join(melDirIn, "melodic_FTmix"))
        and os.path.isfile(os.path.join(melDirIn, "melodic_mix"))
    ):
        print("  - The existing/specified MELODIC directory will be used.")

        if os.path.isdir(os.path.join(melDirIn, "stats")):
            os.symlink(melDirIn, melDir)
        else:
            print(
                "  - The MELODIC directory does not contain the required 'stats' folder. "
                "Mixture modeling on the Z-statistical maps will be run."
            )

            os.makedirs(melDir)
            for item in os.listdir(melDirIn):
                os.symlink(os.path.join(melDirIn, item), os.path.join(melDir, item))

            os.system(
                " ".join(
                    [
                        os.path.join(fslDir, "melodic"),
                        "--in=" + melIC,
                        "--ICs=" + melIC,
                        "--mix=" + melICmix,
                        "--outdir=" + melDir,
                        "--Ostats --mmthresh=0.5",
                    ]
                )
            )
    else:
        if len(melDirIn) != 0:
            if not os.path.isdir(melDirIn):
                print(
                    "  - The specified MELODIC directory does not exist. "
                    "MELODIC will be run seperately."
                )
            else:
                print(
                    "  - The specified MELODIC directory does not contain the required "
                    "files to run ICA-AROMA. MELODIC will be run seperately."
                )

        os.system(
            " ".join(
                [
                    os.path.join(fslDir, "melodic"),
                    "--in=" + inFile,
                    "--outdir=" + melDir,
                    "--mask=" + mask,
                    "--dim=" + str(dim),
                    "--Ostats --nobet --mmthresh=0.5 --report",
                    "--tr=" + str(TR),
                ]
            )
        )

    cmd = " ".join(
        [os.path.join(fslDir, "fslinfo"), melIC, "| grep dim4 | head -n1 | awk '{print $2}'"]
    )
    nrICs = int(float(subprocess.getoutput(cmd)))

    for i in range(1, nrICs + 1):
        zTemp = os.path.join(melDir, "stats", "thresh_zstat" + str(i) + ".nii.gz")
        cmd = " ".join(
            [os.path.join(fslDir, "fslinfo"), zTemp, "| grep dim4 | head -n1 | awk '{print $2}'"]
        )
        lenIC = int(float(subprocess.getoutput(cmd)))

        cmd = " ".join([os.path.join(fslDir, "zeropad"), str(i), "4"])
        ICnum = subprocess.getoutput(cmd)
        zstat = os.path.join(outDir, "thr_zstat" + ICnum)

        os.system(
            " ".join(
                [os.path.join(fslDir, "fslroi"), zTemp, zstat, str(lenIC - 1), "1"]
            )
        )

    os.system(
        " ".join(
            [
                os.path.join(fslDir, "fslmerge"),
                "-t",
                melICthr,
                os.path.join(outDir, "thr_zstat????.nii.gz"),
            ]
        )
    )
    os.system("rm " + os.path.join(outDir, "thr_zstat????.nii.gz"))
    os.system(" ".join([os.path.join(fslDir, "fslmaths"), melICthr, "-mas " + mask, melICthr]))


def register2MNI(fslDir, inFile, outFile, affmat, warp):
    """Register an image or time-series to MNI152 T1 2mm."""
    import os
    import subprocess

    fslnobin = fslDir.rsplit("/", 2)[0]
    ref = os.path.join(fslnobin, "data", "standard", "MNI152_T1_2mm_brain.nii.gz")

    if (len(affmat) == 0) and (len(warp) == 0):
        pixdim1 = float(subprocess.getoutput("%sfslinfo %s | grep pixdim1 | awk '{print $2}'" % (fslDir, inFile)))
        pixdim2 = float(subprocess.getoutput("%sfslinfo %s | grep pixdim2 | awk '{print $2}'" % (fslDir, inFile)))
        pixdim3 = float(subprocess.getoutput("%sfslinfo %s | grep pixdim3 | awk '{print $2}'" % (fslDir, inFile)))

        if (pixdim1 != 2) or (pixdim2 != 2) or (pixdim3 != 2):
            os.system(
                " ".join(
                    [
                        os.path.join(fslDir, "flirt"),
                        " -ref " + ref,
                        " -in " + inFile,
                        " -out " + outFile,
                        " -applyisoxfm 2 -interp trilinear",
                    ]
                )
            )
        else:
            os.system("cp " + inFile + " " + outFile)
    elif (len(affmat) == 0) and (len(warp) != 0):
        os.system(
            " ".join(
                [
                    os.path.join(fslDir, "applywarp"),
                    "--ref=" + ref,
                    "--in=" + inFile,
                    "--out=" + outFile,
                    "--warp=" + warp,
                    "--interp=trilinear",
                ]
            )
        )
    elif (len(affmat) != 0) and (len(warp) == 0):
        os.system(
            " ".join(
                [
                    os.path.join(fslDir, "flirt"),
                    "-ref " + ref,
                    "-in " + inFile,
                    "-out " + outFile,
                    "-applyxfm -init " + affmat,
                    "-interp trilinear",
                ]
            )
        )
    else:
        os.system(
            " ".join(
                [
                    os.path.join(fslDir, "applywarp"),
                    "--ref=" + ref,
                    "--in=" + inFile,
                    "--out=" + outFile,
                    "--warp=" + warp,
                    "--premat=" + affmat,
                    "--interp=trilinear",
                ]
            )
        )


def cross_correlation(a, b):
    """Cross correlations between columns of two matrices."""
    assert a.ndim == b.ndim == 2
    _, ncols_a = a.shape
    return np.corrcoef(a.T, b.T)[:ncols_a, ncols_a:]


def feature_time_series(melmix, mc):
    """Extract the maximum RP correlation feature scores."""
    import random

    mix = np.loadtxt(melmix)
    rp6 = np.loadtxt(mc)
    _, nparams = rp6.shape

    rp6_der = np.vstack((np.zeros(nparams), np.diff(rp6, axis=0)))
    rp12 = np.hstack((rp6, rp6_der))

    rp12_1fw = np.vstack((np.zeros(2 * nparams), rp12[:-1]))
    rp12_1bw = np.vstack((rp12[1:], np.zeros(2 * nparams)))
    rp_model = np.hstack((rp12, rp12_1fw, rp12_1bw))

    nsplits = 1000
    nmixrows, nmixcols = mix.shape
    nrows_to_choose = int(round(0.9 * nmixrows))

    max_correls = np.empty((nsplits, nmixcols))
    for i in range(nsplits):
        chosen_rows = random.sample(population=range(nmixrows), k=nrows_to_choose)
        correl_nonsquared = cross_correlation(mix[chosen_rows], rp_model[chosen_rows])
        correl_squared = cross_correlation(mix[chosen_rows] ** 2, rp_model[chosen_rows] ** 2)
        correl_both = np.hstack((correl_squared, correl_nonsquared))
        max_correls[i] = np.abs(correl_both).max(axis=1)

    return np.nanmean(max_correls, axis=0)


def feature_frequency(melFTmix, TR):
    """Extract the high-frequency content feature scores."""
    Fs = 1 / TR
    Ny = Fs / 2
    FT = np.loadtxt(melFTmix)

    f = Ny * (np.array(list(range(1, FT.shape[0] + 1)))) / (FT.shape[0])
    fincl = np.squeeze(np.array(np.where(f > 0.01)))
    FT = FT[fincl, :]
    f = f[fincl]

    f_norm = (f - 0.01) / (Ny - 0.01)
    fcumsum_fract = np.cumsum(FT, axis=0) / np.sum(FT, axis=0)
    idx_cutoff = np.argmin(np.abs(fcumsum_fract - 0.5), axis=0)
    return f_norm[idx_cutoff]


def feature_spatial(fslDir, tempDir, aromaDir, melIC):
    """Extract the spatial feature scores."""
    import os
    import subprocess

    numICs = int(
        subprocess.getoutput("%sfslinfo %s | grep dim4 | head -n1 | awk '{print $2}'" % (fslDir, melIC))
    )

    edgeFract = np.zeros(numICs)
    csfFract = np.zeros(numICs)
    for i in range(0, numICs):
        tempIC = os.path.join(tempDir, "temp_IC.nii.gz")

        os.system(" ".join([os.path.join(fslDir, "fslroi"), melIC, tempIC, str(i), "1"]))
        os.system(" ".join([os.path.join(fslDir, "fslmaths"), tempIC, "-abs", tempIC]))

        totVox = int(
            subprocess.getoutput(" ".join([os.path.join(fslDir, "fslstats"), tempIC, "-V | awk '{print $1}'"]))
        )

        if not (totVox == 0):
            totMean = float(
                subprocess.getoutput(" ".join([os.path.join(fslDir, "fslstats"), tempIC, "-M"]))
            )
        else:
            print("     - The spatial map of component " + str(i + 1) + " is empty. Please check!")
            totMean = 0

        totSum = totMean * totVox

        csfVox = int(
            subprocess.getoutput(
                " ".join([os.path.join(fslDir, "fslstats"), tempIC, "-k mask_csf.nii.gz", "-V | awk '{print $1}'"])
            )
        )
        if not (csfVox == 0):
            csfMean = float(
                subprocess.getoutput(" ".join([os.path.join(fslDir, "fslstats"), tempIC, "-k mask_csf.nii.gz", "-M"]))
            )
        else:
            csfMean = 0
        csfSum = csfMean * csfVox

        edgeVox = int(
            subprocess.getoutput(
                " ".join([os.path.join(fslDir, "fslstats"), tempIC, "-k mask_edge.nii.gz", "-V | awk '{print $1}'"])
            )
        )
        if not (edgeVox == 0):
            edgeMean = float(
                subprocess.getoutput(" ".join([os.path.join(fslDir, "fslstats"), tempIC, "-k mask_edge.nii.gz", "-M"]))
            )
        else:
            edgeMean = 0
        edgeSum = edgeMean * edgeVox

        outVox = int(
            subprocess.getoutput(
                " ".join([os.path.join(fslDir, "fslstats"), tempIC, "-k mask_out.nii.gz", "-V | awk '{print $1}'"])
            )
        )
        if not (outVox == 0):
            outMean = float(
                subprocess.getoutput(" ".join([os.path.join(fslDir, "fslstats"), tempIC, "-k mask_out.nii.gz", "-M"]))
            )
        else:
            outMean = 0
        outSum = outMean * outVox

        if not (totSum == 0):
            edgeFract[i] = (outSum + edgeSum) / (totSum - csfSum)
            csfFract[i] = csfSum / totSum
        else:
            edgeFract[i] = 0
            csfFract[i] = 0

    os.remove(tempIC)
    return edgeFract, csfFract


def classification(outDir, maxRPcorr, edgeFract, HFC, csfFract):
    """Classify components into motion and non-motion components."""
    import os

    thr_csf = 0.10
    thr_HFC = 0.35
    hyp = np.array([-19.9751070082159, 9.95127547670627, 24.8333160239175])

    x = np.array([maxRPcorr, edgeFract])
    proj = hyp[0] + np.dot(x.T, hyp[1:])
    motionICs = np.squeeze(np.array(np.where((proj > 0) + (csfFract > thr_csf) + (HFC > thr_HFC))))

    np.savetxt(os.path.join(outDir, "feature_scores.txt"), np.vstack((maxRPcorr, edgeFract, HFC, csfFract)).T)

    txt = open(os.path.join(outDir, "classified_motion_ICs.txt"), "w")
    if motionICs.size > 1:
        txt.write(",".join(["{:.0f}".format(num) for num in (motionICs + 1)]))
    elif motionICs.size == 1:
        txt.write("{:.0f}".format(motionICs + 1))
    txt.close()

    txt = open(os.path.join(outDir, "classification_overview.txt"), "w")
    txt.write(
        "\t".join(
            ["IC", "Motion/noise", "maximum RP correlation", "Edge-fraction", "High-frequency content", "CSF-fraction"]
        )
    )
    txt.write("\n")
    for i in range(0, len(csfFract)):
        if (proj[i] > 0) or (csfFract[i] > thr_csf) or (HFC[i] > thr_HFC):
            classif = "True"
        else:
            classif = "False"
        txt.write(
            "\t".join(
                [
                    "{:d}".format(i + 1),
                    classif,
                    "{:.2f}".format(maxRPcorr[i]),
                    "{:.2f}".format(edgeFract[i]),
                    "{:.2f}".format(HFC[i]),
                    "{:.2f}".format(csfFract[i]),
                ]
            )
        )
        txt.write("\n")
    txt.close()

    return motionICs


def denoising(fslDir, inFile, outDir, melmix, denType, denIdx):
    """Denoise the data with FSL regfilt."""
    import os

    check = denIdx.size > 0

    if check == 1:
        if denIdx.size == 1:
            denIdxStrJoin = "%d" % (denIdx + 1)
        else:
            denIdxStr = np.char.mod("%i", (denIdx + 1))
            denIdxStrJoin = ",".join(denIdxStr)

        if (denType == "nonaggr") or (denType == "both"):
            os.system(
                " ".join(
                    [
                        os.path.join(fslDir, "fsl_regfilt"),
                        "--in=" + inFile,
                        "--design=" + melmix,
                        '--filter="' + denIdxStrJoin + '"',
                        "--out=" + os.path.join(outDir, "denoised_func_data_nonaggr.nii.gz"),
                    ]
                )
            )

        if (denType == "aggr") or (denType == "both"):
            os.system(
                " ".join(
                    [
                        os.path.join(fslDir, "fsl_regfilt"),
                        "--in=" + inFile,
                        "--design=" + melmix,
                        '--filter="' + denIdxStrJoin + '"',
                        "--out=" + os.path.join(outDir, "denoised_func_data_aggr.nii.gz"),
                        "-a",
                    ]
                )
            )
    else:
        print(
            "  - None of the components were classified as motion, so no denoising is applied "
            "(a symbolic link to the input file will be created)."
        )
        if (denType == "nonaggr") or (denType == "both"):
            os.symlink(inFile, os.path.join(outDir, "denoised_func_data_nonaggr.nii.gz"))
        if (denType == "aggr") or (denType == "both"):
            os.symlink(inFile, os.path.join(outDir, "denoised_func_data_aggr.nii.gz"))
