# Building Orrery

JUCE and [clap-juce-extensions](https://github.com/free-audio/clap-juce-extensions) are downloaded automatically when
you configure. JUCE is pinned to the commit its tag pointed to when it was chosen: configuring stops if the tag moves.

## Requirements

- CMake 3.22 or later, and Git
- Windows: Visual Studio 17 or 18 with "Desktop development with C++"
- macOS: Xcode
- Linux: GCC or Clang, plus these packages (Ubuntu / Debian names):

  ```bash
  sudo apt install libasound2-dev libjack-jackd2-dev libfreetype-dev libfontconfig1-dev libx11-dev libxcomposite-dev libxcursor-dev libxext-dev libxinerama-dev libxrandr-dev libxrender-dev libxi-dev libglu1-mesa-dev mesa-common-dev
  ```

`-DORRERY_CLAP=OFF` leaves the CLAP versions out (and skips their download). `-DORRERY_TOOLS=OFF` leaves out the measurement
tools, which only matter for the null tests ([CONTRIBUTING.md](../CONTRIBUTING.md)). `-DORRERY_DEV_COPY=OFF` stops the
copy of each VST3 to `build/plugins/<Product name>.vst3` that a DAW's plug-in junction can point at.

## Windows (VST3, CLAP, Standalone)

```bash
cmake -B build -A x64 -DORRERY_TOOLS=OFF
cmake --build build --config Release
```

CMake picks the newest Visual Studio installed. To choose one, add its generator, for example
`-G "Visual Studio 17 2022"`.

Keep the build folder's path short (for example `C:\src\Orrery\build`). JUCE's checkout holds deeply nested
files, and under a long path Git stops with "Filename too long" while configuring.

## macOS (universal AU, VST3, CLAP, Standalone)

```bash
cmake -B build -G Xcode -DORRERY_TOOLS=OFF -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" -DCMAKE_OSX_DEPLOYMENT_TARGET=10.13
cmake --build build --config Release
```

## Linux (VST3, CLAP, Standalone)

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DORRERY_TOOLS=OFF
cmake --build build
```

## Output

Each plug-in lands in `build/<Target>_artefacts/Release/` (`VST3/`, `CLAP/`, `AU/`, `Standalone/`), for example
`build/Scorpius_artefacts/Release/VST3/Scorpius.vst3`. Copy the plug-ins to your plug-in folders, or run a standalone
app from there.

The same build makes the unit tests and the host tests (each VST3 loaded as a DAW loads it, with the saved states
in `plugins/<Id>/tests/data/`); run them with:

```bash
ctest --test-dir build -C Release --output-on-failure
```

## Windows installer

Made with Inno Setup 7 (7.1.1 or newer; the release workflow installs it), from PowerShell after a Release build:

```powershell
pwsh packaging/make_iss_include.ps1 build
iscc /DAppVersion=x.y.z packaging/Orrery.iss
```

The installer lands in `dist/`. Add `/DTestRoot=<folder>` to make a test installer that installs everything under that
folder without administrator rights.

[CONTRIBUTING.md](../CONTRIBUTING.md) describes the tests, the null tests against the originals, the installers and
how releases are made.
