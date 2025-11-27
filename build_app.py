import PyInstaller.__main__
import os
import streamlit
import sys
import subprocess
import shutil
from PyInstaller.utils.hooks import copy_metadata
import zipfile

def prepare_icon():
    """Prepare app icon for packaging.
    - On macOS: prefer 'icon.icns'. If missing but PNG/JPG exists, auto-convert via sips+iconutil.
    - Returns path string to use with --icon, or None.
    """
    if sys.platform != 'darwin':
        # Windows handled by default ICO if present
        if os.path.exists('icon.ico'):
            return 'icon.ico'
        return None

    icns = 'icon.icns'
    if os.path.exists(icns):
        return icns

    # Try common image locations
    candidates = [
        'assets/app_icon.png',
        'assets/app_icon.jpg',
        'icon.png',
        'icon.jpg'
    ]
    src = next((p for p in candidates if os.path.exists(p)), None)
    if not src:
        print("No icon.icns or PNG/JPG found. Proceeding without custom icon.")
        return None

    iconset = 'tmp_icon.iconset'
    try:
        os.makedirs(iconset, exist_ok=True)
        # Generate sizes required by iconutil
        sizes = [
            (16, 16), (32, 32), (128, 128), (256, 256), (512, 512)
        ]
        for base, _ in sizes:
            out = os.path.join(iconset, f'icon_{base}x{base}.png')
            subprocess.run(['sips', '-s', 'format', 'png', '-z', str(base), str(base), src, '--out', out], check=False)
            # Retina @2x
            retina = base * 2
            out2x = os.path.join(iconset, f'icon_{base}x{base}@2x.png')
            subprocess.run(['sips', '-s', 'format', 'png', '-z', str(retina), str(retina), src, '--out', out2x], check=False)

        # Create icns
        subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', icns], check=False)
        if os.path.exists(icns):
            print(f"Generated {icns} from {src}")
            return icns
        else:
            print("iconutil did not produce icon.icns; proceeding without custom icon.")
            return None
    finally:
        try:
            shutil.rmtree(iconset)
        except Exception:
            pass

def build():
    # Get streamlit path to include its static files
    streamlit_path = os.path.dirname(streamlit.__file__)
    
    # Define separator based on OS
    sep = ';' if sys.platform == 'win32' else ':'
    
    # Get metadata for streamlit (fixes PackageNotFoundError)
    metadata = copy_metadata('streamlit')
    
    # Build the PyInstaller arguments
    args = [
        'run_gui.py',  # Your main script
        '--name=NanchengTomatoDownloader',
        '--clean',
        '--noconfirm',
        
        # Include source code
        f'--add-data=src{sep}src',
        
        # Include Streamlit static files
        f'--add-data={streamlit_path}{sep}streamlit',
        
        # Hidden imports often needed by Streamlit
        '--hidden-import=streamlit',
        '--hidden-import=streamlit.web.cli',
        '--hidden-import=streamlit.runtime.scriptrunner.magic_funcs',
        
        # Collect all data/binaries for critical font handling packages
        '--collect-all=brotli',
        '--collect-all=fontTools',
        '--collect-all=browser_cookie3',
        '--collect-all=lz4',
        '--collect-all=pycryptodomex',
    ]
    
    # Add metadata
    for data in metadata:
        args.append(f'--add-data={data[0]}{sep}{data[1]}')
    
    # Build in onedir mode for macOS .app bundles (faster startup, no self-extraction)
    args.append('--onedir')
    
    if sys.platform in ('darwin', 'win32'):
        args.append('--windowed')
    
    # Add icon if available (auto-convert PNG/JPG to ICNS on macOS)
    icon_path = prepare_icon()
    if icon_path:
        args.append(f'--icon={icon_path}')

    print("Starting build with arguments:", args)
    PyInstaller.__main__.run(args)
    print("Build complete! Check the 'dist' folder.")

    # Post-processing: rename app, clear extended attributes, and create DMG/EXE installer
    dist_dir = os.path.join(os.getcwd(), 'dist')
    english_app = os.path.join(dist_dir, 'NanchengTomatoDownloader.app')
    chinese_name = '洋柿子小说下载器.app'
    chinese_app = os.path.join(dist_dir, chinese_name)

    try:
        if os.path.exists(english_app):
            # Clear resource forks to avoid codesign complaints
            try:
                subprocess.run(['xattr', '-cr', english_app], check=False)
            except Exception:
                pass
            # Rename to Chinese app name
            if os.path.exists(chinese_app):
                shutil.rmtree(chinese_app)
            os.rename(english_app, chinese_app)
            print(f"Renamed app to {chinese_name}")
    except Exception as e:
        print(f"Post-rename error: {e}")

    # Create a DMG for macOS
    try:
        if sys.platform == 'darwin' and os.path.exists(chinese_app):
            dmg_tmp = os.path.join(dist_dir, 'dmg_tmp')
            if os.path.exists(dmg_tmp):
                shutil.rmtree(dmg_tmp)
            os.makedirs(dmg_tmp, exist_ok=True)
            # Copy app bundle
            shutil.copytree(chinese_app, os.path.join(dmg_tmp, chinese_name))
            # Add Applications symlink
            applications_link = os.path.join(dmg_tmp, 'Applications')
            try:
                if not os.path.exists(applications_link):
                    os.symlink('/Applications', applications_link)
            except Exception:
                pass

            # Prepare background
            bg_dir = os.path.join(dmg_tmp, '.background')
            os.makedirs(bg_dir, exist_ok=True)
            bg_path = os.path.join(bg_dir, 'dmg_bg.png')
            try:
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (620, 400), (246, 247, 250))
                draw = ImageDraw.Draw(img)
                draw.rectangle([(0,0),(620,400)], fill=(246,247,250))
                draw.rounded_rectangle([(12,12),(608,388)], radius=18, outline=(210,215,225), width=2)
                draw.text((30, 22), "将应用拖到右侧 Applications", fill=(120, 120, 120))
                arrow = [(300, 200), (380, 200), (380, 190), (430, 215), (380, 240), (380, 230), (300, 230)]
                draw.polygon(arrow, fill=(210, 215, 225))
                img.save(bg_path, 'PNG')
            except Exception:
                with open(bg_path, 'wb') as f:
                    f.write(b'')

            # Volume icon (best effort)
            try:
                icns_src = 'icon.icns'
                if os.path.exists(icns_src):
                    shutil.copy(icns_src, os.path.join(dmg_tmp, '.VolumeIcon.icns'))
            except Exception:
                pass

            dmg_rw = os.path.join(dist_dir, 'tmp_rw.dmg')
            dmg_final = os.path.join(dist_dir, '洋柿子小说下载器.dmg')
            for p in [dmg_rw, dmg_final]:
                if os.path.exists(p):
                    try: os.remove(p)
                    except Exception: pass

            subprocess.run(['hdiutil', 'create', '-volname', '洋柿子小说下载器', '-srcfolder', dmg_tmp, '-ov', '-fs', 'HFS+', '-format', 'UDRW', dmg_rw], check=False)
            attach = subprocess.run(['hdiutil', 'attach', '-readwrite', '-noverify', '-noautoopen', dmg_rw], capture_output=True, text=True, check=False)
            mount_point = None
            for line in attach.stdout.splitlines():
                if '/Volumes/' in line:
                    parts = line.split('\t')
                    mount_point = parts[-1].strip()
            if mount_point:
                # Set custom icon (if tool exists)
                subprocess.run(['/usr/bin/SetFile', '-a', 'C', mount_point], check=False)
                # Finder layout via AppleScript
                osa = f'''
                tell application "Finder"
                  set theMount to POSIX file "{mount_point}/.background/dmg_bg.png"
                  set vol to "洋柿子小说下载器"
                  tell disk vol
                    open
                    set current view of container window to icon view
                    set toolbar visible of container window to false
                    set statusbar visible of container window to false
                    set the bounds of container window to {{200, 200, 820, 600}}
                    tell icon view options of container window
                      set icon size to 128
                      set arrangement to not arranged
                      set background picture to theMount
                    end tell
                    set position of file "{chinese_name}" of container window to {{150, 230}}
                    set position of file "Applications" of container window to {{430, 230}}
                    update without registering applications
                    delay 0.5
                    close
                    open
                  end tell
                end tell
                '''
                subprocess.run(['osascript', '-e', osa], check=False)
                subprocess.run(['hdiutil', 'detach', mount_point], check=False)

            subprocess.run(['hdiutil', 'convert', dmg_rw, '-format', 'UDZO', '-o', dmg_final], check=False)
            try:
                os.remove(dmg_rw)
            except Exception:
                pass
            shutil.rmtree(dmg_tmp)
            print(f"DMG created: {dmg_final}")
    except Exception as e:
        print(f"DMG build error: {e}")

    # Create a Windows EXE installer via NSIS (if available), else zip fallback
    try:
        if sys.platform == 'win32':
            app_dir = os.path.join(dist_dir, 'NanchengTomatoDownloader')
            exe_path = os.path.join(app_dir, 'NanchengTomatoDownloader.exe')
            if os.path.exists(exe_path):
                out_installer = os.path.join(dist_dir, 'YangShiziDownloader-Setup.exe')
                nsi_path = os.path.join(dist_dir, 'installer.nsi')
                def winp(p):
                    return os.path.abspath(p).replace('/', '\\')
                app_name_disp = '洋柿子小说下载器'
                install_dir = '$LOCALAPPDATA\\bijianchuanqi'
                nsi = f"""
Unicode true
!include "MUI2.nsh"
Name "{app_name_disp}"
OutFile "{winp(out_installer)}"
InstallDir "{install_dir}"
RequestExecutionLevel user
Page directory
Page instfiles
Section "Install"
  SetOutPath "$INSTDIR"
  File /r "{winp(app_dir)}\\*.*"
  CreateShortcut "$DESKTOP\\{app_name_disp}.lnk" "$INSTDIR\\NanchengTomatoDownloader.exe"
  CreateShortcut "$SMPROGRAMS\\{app_name_disp}\\{app_name_disp}.lnk" "$INSTDIR\\NanchengTomatoDownloader.exe"
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd
Section "Uninstall"
  Delete "$DESKTOP\\{app_name_disp}.lnk"
  RMDir /r "$SMPROGRAMS\\{app_name_disp}"
  RMDir /r "$INSTDIR"
SectionEnd
"""
                try:
                    with open(nsi_path, 'w', encoding='utf-8') as f:
                        f.write(nsi)
                    made = subprocess.run(['makensis', nsi_path], capture_output=True, text=True, check=False)
                except Exception:
                    made = None
                if not os.path.exists(out_installer):
                    zip_path = os.path.join(dist_dir, 'YangShiziDownloader.zip')
                    try:
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                    except Exception:
                        pass
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                        for root, dirs, files in os.walk(app_dir):
                            for name in files:
                                full = os.path.join(root, name)
                                rel = os.path.relpath(full, app_dir)
                                z.write(full, arcname=os.path.join('bijianchuanqi', rel))
                    print(f"Installer tool not found, created zip: {zip_path}")
                else:
                    print(f"Windows installer created: {out_installer}")
    except Exception as e:
        print(f"Windows build error: {e}")

if __name__ == "__main__":
    build()
