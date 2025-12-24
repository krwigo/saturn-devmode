# Camera Notes

```
$ dmesg | grep video
usbcore: registered new interface driver uvcvideo
uvcvideo: Found UVC 1.10 device UC01 HD Camera (a108:2240)
uvcvideo 1-1.3:1.0: Entity type for entity Extension 4 was not initialized!
uvcvideo 1-1.3:1.0: Entity type for entity Processing 2 was not initialized!
uvcvideo 1-1.3:1.0: Entity type for entity Camera 1 was not initialized!
uvcvideo: Found UVC 1.10 device UC01 HD Camera (a108:2240)
uvcvideo: Unable to create debugfs 1-4 directory.
uvcvideo 1-1.3:1.2: Entity type for entity Processing 9 was not initialized!
uvcvideo 1-1.3:1.2: Entity type for entity Camera 8 was not initialized!
```

```
$ lsusb
Bus 002 Device 002: ID 1609:3a04
Bus 001 Device 001: ID 1d6b:0002
Bus 001 Device 004: ID a108:2240 # <--
Bus 001 Device 002: ID 1a86:8091
Bus 002 Device 001: ID 1d6b:0002
Bus 001 Device 003: ID 0bda:c811
```

- USB ID: a108:2240
- Name: UC01 HD Camera
- Driver: uvcvideo

```
$ ls -l /dev/video*
crw-rw---- 1 root root 81, 0 Jan 1 1970 /dev/video0
crw-rw---- 1 root root 81, 1 Jan 1 1970 /dev/video1
```

```
$ ls /sys/class/video4linux/video*
/sys/class/video4linux/video0:
dev dev_debug device index name power subsystem uevent
/sys/class/video4linux/video1:
dev dev_debug device index name power subsystem uevent
```

```
$ head /sys/class/video4linux/video*/name
==> /sys/class/video4linux/video0/name <==
UC01 HD Camera

==> /sys/class/video4linux/video1/name <==
UC01 HD Camera
root@chitu:~$
```

```
$ lsof | grep video
721 /customer/resources/chitu 41 /dev/video0
721 /customer/resources/chitu 42 /dev/video1
```

```
$ ffmpeg -hide_banner -f v4l2 -list_formats all -i /dev/video0
[video4linux2,v4l2 @ 0x510820] Compressed:       mjpeg :          Motion-JPEG : 1920x1080 1280x720 800x600 640x480 640x360
[video4linux2,v4l2 @ 0x510820] Raw       :     yuyv422 :           YUYV 4:2:2 : 640x480 640x360
[video4linux2,v4l2 @ 0x510820] Compressed:        h264 :                H.264 : 1920x1080 1280x720 800x600 640x480 640x360
$ ffmpeg -hide_banner -f v4l2 -list_formats all -i /dev/video1
[video4linux2,v4l2 @ 0x4d0820] Compressed:       mjpeg :          Motion-JPEG : 1920x1080 1280x720 800x600 640x480 640x360
[video4linux2,v4l2 @ 0x4d0820] Raw       :     yuyv422 :           YUYV 4:2:2 : 640x480 640x360
[video4linux2,v4l2 @ 0x4d0820] Compressed:        h264 :                H.264 : 1920x1080 1280x720 800x600 640x480 640x360
```

```
$ ffmpeg -hide_banner -f v4l2 -i /dev/video0 -t 10 -c copy -f null -
Input #0, video4linux2,v4l2, from '/dev/video0':
  Duration: N/A, start: 3752.903086, bitrate: 147456 kb/s
  Stream #0:0: Video: rawvideo (YUY2 / 0x32595559), yuyv422, 640x480, 147456 kb/s, 30 fps, 30 tbr, 1000k tbn, 1000k tbc
Output #0, null, to 'pipe:':
  Metadata:
    encoder         : Lavf58.76.100
  Stream #0:0: Video: rawvideo (YUY2 / 0x32595559), yuyv422, 640x480, q=2-31, 147456 kb/s, 30 fps, 30 tbr, 1000k tbn, 1000k tbc
Stream mapping:
  Stream #0:0 -> #0:0 (copy)
Press [q] to stop, [?] for help
frame=  265 fps= 26 q=-1.0 Lsize=N/A time=00:00:09.99 bitrate=N/A speed=0.997x
video:159000kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: unknown
```

```
$ ffmpeg -hide_banner -codecs | awk 'substr($1,3,1) == "V"'
 ..V... = Video codec
 D.VI.S 012v                 Uncompressed 4:2:2 10-bit
 D.V.L. 4xm                  4X Movie
 D.VI.S 8bps                 QuickTime 8BPS video
 .EVIL. a64_multi            Multicolor charset for Commodore 64 (encoders: a64multi )
 .EVIL. a64_multi5           Multicolor charset for Commodore 64, extended with 5th color (colram) (encoders: a64multi5 )
 D.V..S aasc                 Autodesk RLE
 D.V.L. agm                  Amuse Graphics Movie
 D.VIL. aic                  Apple Intermediate Codec
 DEVI.S alias_pix            Alias/Wavefront PIX image
 DEVIL. amv                  AMV Video
 D.V.L. anm                  Deluxe Paint Animation
 D.V.L. ansi                 ASCII/ANSI art
 DEV..S apng                 APNG (Animated Portable Network Graphics) image
 D.V.L. arbc                 Gryphon's Anim Compressor
 D.V.L. argo                 Argonaut Games Video
 DEVIL. asv1                 ASUS V1
 DEVIL. asv2                 ASUS V2
 D.VIL. aura                 Auravision AURA
 D.VIL. aura2                Auravision Aura 2
 D.V.L. av1                  Alliance for Open Media AV1
 D.V... avrn                 Avid AVI Codec
 DEVI.S avrp                 Avid 1:1 10-bit RGB Packer
 D.V.L. avs                  AVS (Audio Video Standard) video
 ..V.L. avs2                 AVS2-P2/IEEE1857.4
 ..V.L. avs3                 AVS3-P2/IEEE1857.10
 DEVI.S avui                 Avid Meridien Uncompressed
 DEVI.S ayuv                 Uncompressed packed MS 4:4:4:4
 D.V.L. bethsoftvid          Bethesda VID video
 D.V.L. bfi                  Brute Force & Ignorance
 D.V.L. binkvideo            Bink video
 D.VI.. bintext              Binary text
 D.VI.S bitpacked            Bitpacked
 DEVI.S bmp                  BMP (Windows and OS/2 bitmap)
 D.V..S bmv_video            Discworld II BMV video
 D.VI.S brender_pix          BRender PIX image
 D.V.L. c93                  Interplay C93
 D.V.L. cavs                 Chinese AVS (Audio Video Standard) (AVS1-P2, JiZhun profile)
 D.V.L. cdgraphics           CD Graphics video
 D.V..S cdtoons              CDToons video
 D.VIL. cdxl                 Commodore CDXL video
 DEV.L. cfhd                 GoPro CineForm HD
 DEV.L. cinepak              Cinepak
 D.V.L. clearvideo           Iterated Systems ClearVideo
 DEVIL. cljr                 Cirrus Logic AccuPak
 D.VI.S cllc                 Canopus Lossless Codec
 D.V.L. cmv                  Electronic Arts CMV video (decoders: eacmv )
 D.V... cpia                 CPiA video format
 D.VILS cri                  Cintel RAW
 D.V..S cscd                 CamStudio (decoders: camstudio )
 D.VIL. cyuv                 Creative YUV (CYUV)
 ..V.LS daala                Daala
 D.VILS dds                  DirectDraw Surface image decoder
 D.V.L. dfa                  Chronomaster DFA
 DEV.LS dirac                Dirac (encoders: vc2 )
 DEVIL. dnxhd                VC3/DNxHD
 DEVI.S dpx                  DPX (Digital Picture Exchange) image
 D.V.L. dsicinvideo          Delphine Software International CIN video
 DEVIL. dvvideo              DV (Digital Video)
 D.V..S dxa                  Feeble Files/ScummVM DXA
 D.VI.S dxtory               Dxtory
 D.VIL. dxv                  Resolume DXV
 D.V.L. escape124            Escape 124
 D.V.L. escape130            Escape 130
 DEVILS exr                  OpenEXR image
 DEV..S ffv1                 FFmpeg video codec #1
 DEVI.S ffvhuff              Huffyuv FFmpeg variant
 D.V.L. fic                  Mirillis FIC
 DEVI.S fits                 FITS (Flexible Image Transport System)
 DEV..S flashsv              Flash Screen Video v1
 DEV.L. flashsv2             Flash Screen Video v2
 D.V..S flic                 Autodesk Animator Flic video
 DEV.L. flv1                 FLV / Sorenson Spark / Sorenson H.263 (Flash Video) (decoders: flv ) (encoders: flv )
 D.V..S fmvc                 FM Screen Capture Codec
 D.VI.S fraps                Fraps
 D.VI.S frwu                 Forward Uncompressed
 D.V.L. g2m                  Go2Meeting
 D.V.L. gdv                  Gremlin Digital Video
 DEV..S gif                  CompuServe GIF (Graphics Interchange Format)
 DEV.L. h261                 H.261
 DEV.L. h263                 H.263 / H.263-1996, H.263+ / H.263-1998 / H.263 version 2 (decoders: h263 h263_v4l2m2m ) (encoders: h263 h263_v4l2m2m )
 D.V.L. h263i                Intel H.263
 DEV.L. h263p                H.263+ / H.263-1998 / H.263 version 2
 DEV.LS h264                 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (decoders: h264 h264_v4l2m2m ) (encoders: libx264 libx264rgb h264_v4l2m2m )
 D.VIL. hap                  Vidvox Hap
 DEV.L. hevc                 H.265 / HEVC (High Efficiency Video Coding) (decoders: hevc hevc_v4l2m2m ) (encoders: hevc_v4l2m2m )
 D.V.L. hnm4video            HNM 4 video
 D.VIL. hq_hqa               Canopus HQ/HQA
 D.VIL. hqx                  Canopus HQX
 DEVI.S huffyuv              HuffYUV
 D.VI.S hymt                 HuffYUV MT
 D.V.L. idcin                id Quake II CIN video (decoders: idcinvideo )
 D.VI.. idf                  iCEDraw text
 D.V.L. iff_ilbm             IFF ACBM/ANIM/DEEP/ILBM/PBM/RGB8/RGBN (decoders: iff )
 D.V.L. imm4                 Infinity IMM4
 D.V.L. imm5                 Infinity IMM5
 D.V.L. indeo2               Intel Indeo 2
 D.V.L. indeo3               Intel Indeo 3
 D.V.L. indeo4               Intel Indeo Video Interactive 4
 D.V.L. indeo5               Intel Indeo Video Interactive 5
 D.V.L. interplayvideo       Interplay MVE video
 D.VIL. ipu                  IPU Video
 DEVILS jpeg2000             JPEG 2000
 DEVILS jpegls               JPEG-LS
 D.VIL. jv                   Bitmap Brothers JV video
 D.V.L. kgv1                 Kega Game Video
 D.V.L. kmvc                 Karl Morton's video codec
 D.VI.S lagarith             Lagarith lossless
 .EVI.S ljpeg                Lossless JPEG
 D.VI.S loco                 LOCO
 D.V.L. lscr                 LEAD Screen Capture
 D.VI.S m101                 Matrox Uncompressed SD
 D.V.L. mad                  Electronic Arts Madcow Video (decoders: eamad )
 DEVI.S magicyuv             MagicYUV video
 D.VIL. mdec                 Sony PlayStation MDEC (Motion DECoder)
 D.V.L. mimic                Mimic
 DEVIL. mjpeg                Motion JPEG
 D.VIL. mjpegb               Apple MJPEG-B
 D.V.L. mmvideo              American Laser Games MM Video
 D.V.L. mobiclip             MobiClip Video
 D.V.L. motionpixels         Motion Pixels video
 DEV.L. mpeg1video           MPEG-1 video (decoders: mpeg1video mpeg1_v4l2m2m )
 DEV.L. mpeg2video           MPEG-2 video (decoders: mpeg2video mpegvideo mpeg2_v4l2m2m )
 DEV.L. mpeg4                MPEG-4 part 2 (decoders: mpeg4 mpeg4_v4l2m2m ) (encoders: mpeg4 mpeg4_v4l2m2m )
 D.V.L. msa1                 MS ATC Screen
 D.VI.S mscc                 Mandsoft Screen Capture Codec
 D.V.L. msmpeg4v1            MPEG-4 part 2 Microsoft variant version 1
 DEV.L. msmpeg4v2            MPEG-4 part 2 Microsoft variant version 2
 DEV.L. msmpeg4v3            MPEG-4 part 2 Microsoft variant version 3 (decoders: msmpeg4 ) (encoders: msmpeg4 )
 D.VI.S msp2                 Microsoft Paint (MSP) version 2
 D.V..S msrle                Microsoft RLE
 D.V.L. mss1                 MS Screen 1
 D.VIL. mss2                 MS Windows Media Video V9 Screen
 DEV.L. msvideo1             Microsoft Video 1
 D.VI.S mszh                 LCL (LossLess Codec Library) MSZH
 D.V.L. mts2                 MS Expression Encoder Screen
 D.V.L. mv30                 MidiVid 3.0
 D.VIL. mvc1                 Silicon Graphics Motion Video Compressor 1
 D.VIL. mvc2                 Silicon Graphics Motion Video Compressor 2
 D.V.L. mvdv                 MidiVid VQ
 D.VIL. mvha                 MidiVid Archive Codec
 D.V..S mwsc                 MatchWare Screen Capture Codec
 D.V.L. mxpeg                Mobotix MxPEG video
 D.VIL. notchlc              NotchLC
 D.V.L. nuv                  NuppelVideo/RTJPEG
 D.V.L. paf_video            Amazing Studio Packed Animation File Video
 DEVI.S pam                  PAM (Portable AnyMap) image
 DEVI.S pbm                  PBM (Portable BitMap) image
 DEVI.S pcx                  PC Paintbrush PCX image
 DEVI.S pfm                  PFM (Portable FloatMap) image
 DEVI.S pgm                  PGM (Portable GrayMap) image
 DEVI.S pgmyuv               PGMYUV (Portable GrayMap YUV) image
 D.VI.S pgx                  PGX (JPEG2000 Test Format)
 D.V.L. photocd              Kodak Photo CD
 D.VIL. pictor               Pictor/PC Paint
 D.VIL. pixlet               Apple Pixlet
 DEV..S png                  PNG (Portable Network Graphics) image
 DEVI.S ppm                  PPM (Portable PixelMap) image
 DEVIL. prores               Apple ProRes (iCodec Pro) (encoders: prores prores_aw prores_ks )
 D.VIL. prosumer             Brooktree ProSumer Video
 D.VI.S psd                  Photoshop PSD file
 D.VIL. ptx                  V.Flash PTX image
 D.VI.S qdraw                Apple QuickDraw
 D.V.L. qpeg                 Q-team QPEG
 DEV..S qtrle                QuickTime Animation (RLE) video
 DEVI.S r10k                 AJA Kona 10-bit RGB Codec
 DEVI.S r210                 Uncompressed RGB 10-bit
 D.V.L. rasc                 RemotelyAnywhere Screen Capture
 DEVI.S rawvideo             raw video
 D.VIL. rl2                  RL2 video
 DEV.L. roq                  id RoQ video (decoders: roqvideo ) (encoders: roqvideo )
 DEV.L. rpza                 QuickTime video (RPZA)
 D.V..S rscc                 innoHeim/Rsupport Screen Capture Codec
 DEV.L. rv10                 RealVideo 1.0
 DEV.L. rv20                 RealVideo 2.0
 D.V.L. rv30                 RealVideo 3.0
 D.V.L. rv40                 RealVideo 4.0
 D.V.L. sanm                 LucasArts SANM/SMUSH video
 D.V.LS scpr                 ScreenPressor
 D.V..S screenpresso         Screenpresso
 D.V.L. sga                  Digital Pictures SGA Video
 DEVI.S sgi                  SGI image
 D.VI.S sgirle               SGI RLE 8-bit
 D.VI.S sheervideo           BitJazz SheerVideo
 D.V.L. simbiosis_imx        Simbiosis Interactive IMX Video
 D.V.L. smackvideo           Smacker video (decoders: smackvid )
 D.V.L. smc                  QuickTime Graphics (SMC)
 D.VIL. smvjpeg              Sigmatel Motion Video
 DEV.LS snow                 Snow
 D.VIL. sp5x                 Sunplus JPEG (SP5X)
 DEVIL. speedhq              NewTek SpeedHQ
 D.VI.S srgc                 Screen Recorder Gold Codec
 DEVI.S sunrast              Sun Rasterfile image
 ..V..S svg                  Scalable Vector Graphics
 DEV.L. svq1                 Sorenson Vector Quantizer 1 / Sorenson Video 1 / SVQ1
 D.V.L. svq3                 Sorenson Vector Quantizer 3 / Sorenson Video 3 / SVQ3
 DEVI.S targa                Truevision Targa image
 D.VI.S targa_y216           Pinnacle TARGA CineWave YUV16
 D.V.L. tdsc                 TDSC
 D.V.L. tgq                  Electronic Arts TGQ video (decoders: eatgq )
 D.V.L. tgv                  Electronic Arts TGV video (decoders: eatgv )
 D.V.L. theora               Theora
 D.VIL. thp                  Nintendo Gamecube THP video
 D.V.L. tiertexseqvideo      Tiertex Limited SEQ video
 DEVI.S tiff                 TIFF image
 D.VIL. tmv                  8088flex TMV
 D.V.L. tqi                  Electronic Arts TQI video (decoders: eatqi )
 D.V.L. truemotion1          Duck TrueMotion 1.0
 D.V.L. truemotion2          Duck TrueMotion 2.0
 D.VIL. truemotion2rt        Duck TrueMotion 2.0 Real Time
 D.V..S tscc                 TechSmith Screen Capture Codec (decoders: camtasia )
 D.V.L. tscc2                TechSmith Screen Codec 2
 D.VIL. txd                  Renderware TXD (TeXture Dictionary) image
 D.V.L. ulti                 IBM UltiMotion (decoders: ultimotion )
 DEVI.S utvideo              Ut Video
 DEVI.S v210                 Uncompressed 4:2:2 10-bit
 D.VI.S v210x                Uncompressed 4:2:2 10-bit
 DEVI.S v308                 Uncompressed packed 4:4:4
 DEVI.S v408                 Uncompressed packed QT 4:4:4:4
 DEVI.S v410                 Uncompressed 4:4:4 10-bit
 D.V.L. vb                   Beam Software VB
 D.VI.S vble                 VBLE Lossless Codec
 D.V.L. vc1                  SMPTE VC-1 (decoders: vc1 vc1_v4l2m2m )
 D.V.L. vc1image             Windows Media Video 9 Image v2
 D.VIL. vcr1                 ATI VCR1
 D.VIL. vixl                 Miro VideoXL (decoders: xl )
 D.V.L. vmdvideo             Sierra VMD video
 D.V..S vmnc                 VMware Screen Codec / VMware Video
 D.V.L. vp3                  On2 VP3
 D.V.L. vp4                  On2 VP4
 D.V.L. vp5                  On2 VP5
 D.V.L. vp6                  On2 VP6
 D.V.L. vp6a                 On2 VP6 (Flash version, with alpha channel)
 D.V.L. vp6f                 On2 VP6 (Flash version)
 D.V.L. vp7                  On2 VP7
 DEV.L. vp8                  On2 VP8 (decoders: vp8 vp8_v4l2m2m ) (encoders: vp8_v4l2m2m )
 D.V.L. vp9                  Google VP9 (decoders: vp9 vp9_v4l2m2m )
 ..V.L. vvc                  H.266 / VVC (Versatile Video Coding)
 D.V..S wcmv                 WinCAM Motion Video
 D.VILS webp                 WebP
 DEV.L. wmv1                 Windows Media Video 7
 DEV.L. wmv2                 Windows Media Video 8
 D.V.L. wmv3                 Windows Media Video 9
 D.V.L. wmv3image            Windows Media Video 9 Image
 D.VIL. wnv1                 Winnov WNV1
 DEV..S wrapped_avframe      AVFrame to AVPacket passthrough
 D.V.L. ws_vqa               Westwood Studios VQA (Vector Quantized Animation) video (decoders: vqavideo )
 D.V.L. xan_wc3              Wing Commander III / Xan
 D.V.L. xan_wc4              Wing Commander IV / Xxan
 D.VI.. xbin                 eXtended BINary text
 DEVI.S xbm                  XBM (X BitMap) image
 DEVIL. xface                X-face image
 D.VI.S xpm                  XPM (X PixMap) image
 DEVI.S xwd                  XWD (X Window Dump) image
 DEVI.S y41p                 Uncompressed YUV 4:1:1 12-bit
 D.VI.S ylc                  YUY2 Lossless Codec
 D.V.L. yop                  Psygnosis YOP Video
 DEVI.S yuv4                 Uncompressed packed 4:2:0
 D.V..S zerocodec            ZeroCodec Lossless Video
 DEVI.S zlib                 LCL (LossLess Codec Library) ZLIB
 DEV..S zmbv                 Zip Motion Blocks Video
```
