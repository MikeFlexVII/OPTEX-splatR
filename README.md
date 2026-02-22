# OPTEX-splatR v0.5.0 Alpha (CPU Only) - 🍎 SHARP for Win10/11

A super slow implementation of Apple's `ml-sharp` that runs natively on Windows 10/11 with minimal configuration. 
This application acts as a standalone GUI wrapper that automatically downloads the necessary models and generates 3D Gaussian Splats from a single image.

## ✨ Features

**Auto-Model Download:** Automatically fetches the required PyTorch models upon first run.
**Focal Length Pre-processing:** Fine-tune your image parameters before generation.
**Adjustable Spherical Harmonics (SH):** Lower the SH level (0-3) before export to significantly minimize `.ply` file sizes—perfect for web and streaming use.
**Instant 3D Preview:** Review your results immediately in a pop-up 3D `.ply` viewer.

## ⚡ Performance & Quality

**Speed:** Basic generation currently takes a few minutes per image on CPU. (Note: Speed will increase drastically in future GPU-accelerated builds).
**Quality:** Upon inspection, output quality appears highly comparable to other splatting platforms. 
**File Size:** Expect approximately ~63MB per exported `.ply` file at default/high settings.

## ⚠️ License and Usage Restrictions

The graphical user interface (GUI) code in this repository (`app.py`, `sh_filter.py`, etc.) is open-sourced under the **MIT License**. 

**IMPORTANT DISCLAIMER REGARDING ML-SHARP:**
This application acts as a frontend wrapper for Apple's `ml-sharp` model. While this GUI is open-source, the underlying `ml-sharp` model weights downloaded and utilized by this software are subject to Apple's **Non-Commercial Research License**. 

By using this software, you agree to abide by Apple's terms. The generated 3D Gaussian Splats and the model itself may **only be used for non-commercial research purposes**. You may not use this software, or the 3D models it generates, for any commercial products, services, or exploitation. 

For full details, please review [Apple's Model License](https://github.com/apple/ml-sharp/blob/main/LICENSE_MODEL).
