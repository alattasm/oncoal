# Lip sync (Wav2Lip, CPU)

Patched `inference.py` from https://github.com/Rudrabha/Wav2Lip (weights: wav2lip_gan.pth, s3fd.pth).
Changes: librosa mel keyword args, `torch.load(weights_only=False)`, and frames with no detected face
reuse the nearest detected face box (cartoon faces / hands over face).

    python3 inference.py --checkpoint_path checkpoints/wav2lip_gan.pth --face src_loop.mp4 \
        --audio vocals_16k.wav --outfile src_lipsync.mp4 --pads 0 15 0 0 --face_det_batch_size 4 \
        --wav2lip_batch_size 64 --nosmooth
    SHORT_DUR=45 python3 ../short.py src_lipsync.mp4
