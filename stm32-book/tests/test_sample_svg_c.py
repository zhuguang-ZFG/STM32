from __future__ import annotations

import hashlib
import importlib.util
import re
import unittest
from pathlib import Path


BOOK_DIR = Path(__file__).resolve().parents[1]
REPO = BOOK_DIR.parent
BUILD_PATH = BOOK_DIR / "build_html.py"


def text_file_hash(path: Path) -> str:
    """sha256 of a text file with CRLF folded to LF, so a Windows checkout matches."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

ROWS = """
animations/adc-sar.svg 900x620 21944 3668b84ef86909dbfcd2141c0dad9b9b15645ee29174f0e15171b8cf9bc696e8
animations/boot-sequence.svg 900x620 15447 9002177f51c55fc20e4f3d6b2549a3d1066338b609c594202426139ac35731b9
animations/can-arbitration.svg 900x620 25142 6a68426929c8ad0f4046b091ae4be6db894eba2e4125f1e03c41c695167a3176
animations/clock-tree.svg 900x620 11697 c0e07c5c01bffae9769331541bdf87dcfc4ea61e3b4081b6f72834b476fbed08
animations/debug-swo.svg 900x620 12733 e44f13c22225782401c9b3d44f376781297c0103040118786626621476a6ffdd
animations/dma-circular.svg 900x620 13433 1ca52dc381d7a3a909ad9f543ded30d24d6bb44b8e50714524ef2723be80a0a6
animations/flash-iap.svg 900x620 13007 55ad4b20f25654a8bb6a705303a99d5fb513f5b125b70a4545278f84d63ad0cb
animations/freertos-scheduler.svg 900x620 15472 dac2433cc885374c2ce49ff93bf8dd67c9c853b3ee0784a0e0f7e42abded78d9
animations/g0-boot-swd.svg 900x620 12440 1bff8776ad1ace5ee07c1bd9a5cc861ca92c9c84a721600a35734095bca7e353
animations/gpio-blink.svg 900x620 14629 81690ee196c303d2ee445ccc78f2d05a0b153627d7b07fae4a6d84ca77c3c721
animations/gpio-input-interrupt.svg 900x620 13733 91523ae894f3e4a3be9f06e11dd804a058d5919786a9a084b19dc69dd74d24e6
animations/h7-clock-chain.svg 900x620 11808 4edcb50a1871b7dd97c5a86685f43b5884c92aec162c53aa478f519394dc2068
animations/i2c-transaction.svg 900x620 23087 db636a1ff816a0387a77e985e074251d3f0deaec5459b24d4c1c579e1fb5f86b
animations/iwdg-window.svg 900x620 10861 324f8c83215265a9e4b9c256552019165c14adb914c3fc9189f054f264751444
animations/l4-stop2-evidence.svg 900x620 14214 04228f72309b692ff19fdbccce10fe8a7fc1a1030af9f83bba0307fc7896bd1e
animations/lowpower-wakeup.svg 900x620 11994 83dcdc3ef4ba4085200d8da3582c3c977a5b28b6f5d47a5cdd8224d7dd729087
animations/memory-map.svg 900x620 8004 82e9be18ac7ecbe388e478b995ef9bcf8e876a2373406565469fda41e911b11f
animations/network-online-state.svg 900x620 12028 b411a492adbc81a722ace75d62461b5b21a8c97a364d0f253fb43e1b09df8fdb
animations/network-packet-journey.svg 900x620 19675 bf0e59bfccaab4cd6979f22a731a6997fb5d3d3bca21b22d62e9191219748a2c
animations/nvic-interrupt-flow.svg 900x620 16051 4d5c80108121e58ca5c236b0617b52ce212cfa76bee5d7c96ddf2e17008385cf
animations/rtos-startup-gates.svg 900x620 14083 8e65b6e47917be3fdd79f4b51834520927b144caa4ed12b6d392e21823464b3b
animations/rtos-system-layers.svg 900x620 14831 dddb4298e770defc39f89d561bcff94279facb1e5309f869b92fb8b801d509fb
animations/sample-00-boot-fetch-flow.svg 900x620 12449 c3a3d6c6349724501fb073ba40efcab344a595bf015d2933960d2423558ad2f4
animations/sample-01-flash-swd-flow.svg 900x620 12446 2f2c8f274d075eec858801b7747f581e83cac8a86b23fa61f654d889af0d94d0
animations/sample-02-pll-lock-flow.svg 900x620 11446 3d8b2716cc664bb71a9f3e27abfd646db5c3ebd34fe7cbd3dbb60ec9f4fe769b
animations/sample-03-gpio-bsrr-flow.svg 900x620 9618 ead08cad37fff01490142f2a28b925468502dbd62b9141978913277c9d332ed4
animations/sample-04-nvic-preempt-flow.svg 900x620 12598 87e309312f1025e2de38ea0266832a1b8a58c13206f2d4d77d9a0adc78bce3d9
animations/sample-05-pwm-edge-flow.svg 900x620 9893 91b5019ada07f3750ad0a2cd9fc81dbdc9885065d1b433862da22f1a6d2549d6
animations/sample-06-uart-baud-wire.svg 900x620 16145 97ca1000a2361f44ddd9b5c10cf82708c621f5e3f638cd09bc27557215e12f4e
animations/sample-07-i2c-ack-flow.svg 900x620 12425 7a99ec37e70b0551940dad29b77e20e0715c6d598354bcc2a6e13c412ce681e5
animations/sample-08-spi-jedec-flow.svg 900x620 12505 a9aa29411b1f77c1904b235f9c93b293d0adcc234b836533013037162bcaec57
animations/sample-09-adc-sar-weights.svg 900x620 14849 e39f754a56549a0438cd616d60d7888759b4c8dd80f582f205cf971b7a80ef40
animations/sample-10-dma-circular-ht.svg 900x620 9941 ce79db41f9172b5fd45d210c320339c720c2fa046100ed0b497987a98de3a5cb
animations/sample-11-iwdg-feed-flow.svg 900x620 12430 b2f0f5b06accd15edd555be102020e99785e8453c2f98e3f05988cf1653fd627
animations/sample-12-iap-jump-flow.svg 900x620 12467 a2278d2c320a80ae5550bda20ec02c20cca61178ccb2a63aaaff316fc968765a
animations/sample-13-can-arb-flow.svg 900x620 12423 b45bd81edac827b659601482baf202f6bfe7e9e0201cb3792df6568861c9cfc9
animations/sample-14-usb-48m-flow.svg 900x620 12452 107c0d23a8af44c712191d23bc06ef4e9aefc3ee69038549537246d6fe8be09c
animations/sample-15-rtos-tick-flow.svg 900x620 12460 4d5c39f47b4bb681ff857b0fc53e9b0fd85db83ae2314d69e44c26fd97e17017
animations/sample-16-stop-wake-flow.svg 900x620 12462 450d807c330534f310c7f3d317aceeaa2eda4c4635a16f09d86b11f5a0dcda6d
animations/sample-17-cfsr-flow.svg 900x620 12422 8455dc285d03959e4007d4c725b5d5160b4f9b6b48efed6a1097d59c311b1c54
animations/sample-18-boot0-flow.svg 900x620 12381 bee279230c2bd166e7f1166509be25271e9e97d8d9452bcdbcac7dea707ce090
animations/sample-19-slot-fill-flow.svg 900x620 12364 e0fd9282611a21e24a3b229723a67ae23ef41f832f58d3ee2b7f68eae6841039
animations/sample-20-evidence-flow.svg 900x620 12387 5d0ae27dcf1bf67fd51d8e367041a3e46b0855f6e7edd8478d6c69aea21020fd
animations/sample-20-lookup-flow.svg 900x620 13330 31fd3cd26a383eb0c9af27c1426564d827322c1e57e8c71b9c4bdb516f23fdf9
animations/sample-21-crystal-boot-flow.svg 900x620 12410 d3ee93e687a24642cba3951e23dd5ec60d6105113a982d638ce552c868a2b065
animations/sample-21-power-swd.svg 900x620 13237 f7bca2108dac36c6962306c4529209c9dcc52a1ea18836d692cfdbcc28786745
animations/sample-22-sim-pick-flow.svg 900x620 12377 50000cca48d0a33517000481a9cae877128c1e49949bd5e697f748310e5b15e2
animations/sample-23-boot-latch.svg 900x620 10798 c4686bd2a828dd287175a6333043848ca35bbef1105725177998da60406bde8e
animations/sample-23-boot-source-flow.svg 900x620 12487 9ddb0738b19e4d90d0d09c222002965180bbe6de643a58ee1b69f4ab3752c4ee
animations/sample-24-wake-restore-flow.svg 900x620 12385 d33869e6fd8e65d6a13da3647d2cf598e9d2ca0ec8b36c844136936fda1b05cf
animations/sample-25-hse-to-480-flow.svg 900x620 12393 a795b3c7e41d8c746e2a4499c6ae7d356a81a57dffd4b14781536965ce4c3900
animations/sample-26-clk-cfg-en-flow.svg 900x620 12399 1d145cce8706ff787eaf1b225c680569ce83c80f85726d4bbba57d3d10ed71bb
animations/sample-27-link-dhcp-flow.svg 900x620 12389 66aa93e8307316606e806b408842d5b783b63bf1121be0c0bf9811f383cef909
animations/sample-28-isr-owner-flow.svg 900x620 12420 aa875db87c818c54d6152e2611feec274628cdcab0207b8e2239e0261cd27f75
animations/sample-28-owner-flow.svg 900x620 13550 751e413262886ed40075c2623f83eb4093ee0d7647df09572c624968aa1fb324
animations/sample-f-repo-lane-flow.svg 900x620 12404 dbfa548a78f0e7865cd806cbe25a7a494e7980a624256fbd2aceb5b8731ca66b
animations/simulation-acceptance-gates.svg 900x620 10660 c0316576a9b8a6c45011d4a1fce3f884228ffa2a0788561d983b43227aa9e146
animations/spi-transfer.svg 900x620 21147 579ddd86d159809dc4c667a0bf1faf652c1c0538d4d155f6f7187896df7a3968
animations/spl-init-pipeline.svg 900x620 11903 d1ebfca0e4b6e9cbbda864bf9c82f217976ad6b8e16bee53e36059b6d6e8885c
animations/timer-modes.svg 900x620 11885 c8a1e34469293d5f4a02a5703271bcf62fc4e9f2f1e89429dbcaa02b56ebeabf
animations/timer-pwm.svg 900x620 10208 54833bf0841b1569cb993934699473b2ee4d2f0ed56b858a4fb9b5855bb8532f
animations/toolchain-flow.svg 900x620 15372 e131ad994e16c099c15d4d941c0e7aade4865c53c912248a73590e939645e0bd
animations/uart-frame.svg 900x620 18789 a696fc8932d337f1b22dacef54ecfe01dd37aa963b41d67111c584122f6b3400
animations/uart-idle-dma.svg 900x620 14001 c6d21a244ac4ef329cbb5c06dad31205d18c57e8444a326159f4625b08c6f308
animations/usb-enumeration.svg 900x620 16705 ccf597d223d3d29cf8f5c3cbc47709d384453048753e4725cad655e84e7b0a1d
boards/blackpill-stm32f411ce.svg 900x620 32342 511d86c80d8862e78be2a0c7e6ca7e24e1db11d30ea66d47b3b2f1e8cdec0494
boards/bluepill-stm32f103c8t6.svg 900x620 35752 8f4d1581c6b4ba6391e840df71383291501327d827deacfedb057e59abb4f429
boards/f103zet6-dev.svg 900x620 26435 e3dbb3e02afe0cbf1f9040e0c438289cb2038c6244a128d9c07d7b9aa0679a25
boards/f4-discovery.svg 900x620 26480 38d9fc620839b504c7a965b1962fb995a46e8068adcc645ab444370fd4143826
boards/nucleo-f411re.svg 900x620 21539 e52ce8055d27e38a2ce8d09dce5fb601a447c972e995440108961cceaefcbf05
boards/peripheral-wiring.svg 900x620 14177 f7210ea4e61af5bda0d90d25655395c10af97c67f6910d50878150a81693cff5
boards/pinout-bluepill.svg 900x620 33856 9ec78f08a53e93daaa169ccd6f7d180dbc3a783d61b7b4b3e0dc394fdc21545c
boards/pinout-stm32g071rb-lqfp64.svg 620x750 34735 7ccc8b702e15d0473bfc1d4c956397dfbb5bd50363d4e762bd100c794d1d2193
boards/pinout-stm32h743zi-lqfp144.svg 840x970 76238 4d71ec5cab732513073bac6721ae4c688a36f18ab11fcae4b5e6e927433b7a96
boards/pinout-stm32l476rg-lqfp64.svg 620x750 34720 a5a8468d7b087956a4635ac7c88412f1e7920570c53e388e0a10a44fbe5f8adf
diagrams/classic-03-bitband.svg 960x660 10962 802dd2de3ba9b21add09a8e7cb6e459ebca21b1ed2722d654666bdc922cedaf0
diagrams/classic-03-debounce.svg 960x660 11186 6bd1b7b8c6f2e744830ccdb5aefe0f3276d291a0fe5c81f5bf0186030c8798d7
diagrams/classic-03-ft-evidence.svg 960x660 8266 f1697e2aba1a0b826e98324eed0bfc1ef975e36446d30ae130393673c6ff76b9
diagrams/classic-03-init-code.svg 960x660 9108 b1a622b9fc6d34d668cb3be4bd0caa19f50179f5fdcc7c6c0e77b20fa2f39f3a
diagrams/classic-03-open-drain.svg 960x660 14389 f82fdd1683523576bcb37ba9f77660ae4fb10c8643487d10dac5444a7c52ec74
diagrams/classic-03-pa0-pa1-wiring.svg 960x660 11103 207a23c9c085d9aac37b710034a5a1101d3d4a4e9cc85e55614af2e56bb16070
diagrams/classic-03-pc13-evidence.svg 960x660 10667 687969113f8f812f901bdfeec8d6751fb8f3feda884364f8b646c0580babf5d2
diagrams/classic-03-polling.svg 960x660 9798 a126b851e13cfdf196d89eecc8dadd2fdc7ce9fe17aeac87d0d4d3c5dbfab65f
diagrams/classic-03-register-map.svg 960x660 12019 c9f7f9646798ee2cc43bf0b8c021efbef8d9b3e8bfdff5f29b5adf6ce5cadd1c
diagrams/classic-03-remap.svg 960x660 9123 59d6d6a9a552b797394cc67593739fb944ecd8609febd7c4c290bee85ccd05d1
diagrams/classic-03-write-methods.svg 960x660 10503 9bbc68ad681faeadd134ef89c10528eea8378b16f240397c437971b55850c960
diagrams/dma-buffer-ownership.svg 900x560 9298 f33f98d257e04ac2054f8e076c9401ff4aa9d91f30ebc32b474a08329e1b5439
diagrams/fault-triage-ladder.svg 900x560 10278 ef5120ac9bbc4ccdc40c77db5255baf74dc03e281ac73e2b654370d851282a34
diagrams/firmware-stack-choice.svg 900x560 8495 ffad6ce257492aef37d37dce681845652b67c5b6f5d341cc279c5ea8c02c9d1e
diagrams/first-lab-wiring.svg 900x560 9942 b44f10ed4e72897cc4261b79bd22e34287ecc222868e131c77b067cc6a0d0df6
diagrams/first-success-gates.svg 900x560 9213 8ad973a0bd59ecec057885587cc9d6476ed3f2506be55629220ad93dec561963
diagrams/h7-pinmux-conflicts.svg 900x560 7106 422b66ce1b659f837216d750bf10f80f96b6a530f2b2fca6902ed1ef011a1632
diagrams/h7-power-domains.svg 900x560 7154 d0da1b09891335ae1afac71e6beacd6d00a43a9d3151e6838eed336ea3cfb69d
diagrams/h7-revision-clock-decision.svg 900x560 5940 7e7f3f5dc844f2c1e9e3e02506b4797dfd75a6723145dd17a3be4823bb2a5e29
diagrams/h7-startup-evidence.svg 900x560 7720 d0bed6f9b648d7755ecc13a1c0d1123ea6f014332e4ad5982b5733f602fea29a
diagrams/iap-acceptance-gates.svg 900x560 9398 0f4a6a1d0b50ba2cd5ecb820a736639b669f50d94f2f751253e89f52f2249d3b
diagrams/instrument-evidence-ladder.svg 900x560 6398 17eb1364f9b45c92a06969a294b1f31180503cd3879200f8ce8209ce1229c510
diagrams/interrupt-priority.svg 900x560 11942 7f3d8b282ed7342a56b598694137c3091ca4bd4a10acc73cd5a651a9b0c7fe05
diagrams/l4-idd-bench.svg 900x560 8736 e7fb7cbbf8f803d0f622784493ecb16f0596565606f77ef6f757d3559900d66f
diagrams/layers-hal-ll-reg.svg 900x560 10453 2ce7570576e925d07d9451923568c2e1143152044e151a7d0e3a9125273f620f
diagrams/lowpower-current-evidence.svg 900x560 6553 b179af76c293ac0d9ba059570b55a2b83bdc82f077d74387c85581f25765d3e6
diagrams/manual-choice-map.svg 900x560 9687 75a6977234623a1b9e8edbd6129863f67cd9ab3ad4a4eeec7e55abe96fece3e9
diagrams/network-cache-ownership.svg 900x560 10014 5e743984bd7bf6e68f539020ac23d5a7498e89ac1788e6a3d1245c47b94daf85
diagrams/network-debug-ladder.svg 900x560 11338 a1405054a5ba593090ad0bc6fdb104a5c8e513dd9695bd35767867faeeaec2e8
diagrams/peripheral-bus.svg 900x560 14143 80d659d44758f54a352b8447fb4a49e6fa880a47cb981bc487c1d69aaa6ae2f6
diagrams/project-structure.svg 900x560 13031 53f68cd4e58288a346e7cd09867724a75daa564e3b527a46a67627250def2acf
diagrams/rtos-config-paths.svg 900x560 12512 02d7b84ba4c8fe73dcf6ea89937dfc0ebb995f7d782164fa36ba8748e708d80c
diagrams/rtos-deadline-budget.svg 900x560 8875 eec759b57c52c884ef1d126b8a0a139cb9e450dbfa561a5cb0af0467e6cb561f
diagrams/rtos-owner-task.svg 900x560 8947 0023f1657fb272cc36e19156764f8a6a4cf5a6417bff26ef764a979f7b4d32eb
diagrams/sample-00-accept-gate.svg 960x860 9596 487806482cb3425ed05fece88056fc3a1c1cf4fe38ed27c4815b5446be92129d
diagrams/sample-00-boot-state.svg 960x620 7142 41eff7ecd092c9f1d0e41629b4b87f337ea9d27e4b63f3ddda1d03e96c3eb3b1
diagrams/sample-00-boot-triage.svg 960x970 10066 a9459d49838934d93ceb23b754cd24d98204533b91876828b19371d1ec0707dc
diagrams/sample-00-learn-loop.svg 960x860 12080 f6e3cb6fb26e7495c348d26bd11143a1c181c3efe45e67975bea9bc970d6a728
diagrams/sample-00-roadmap-gates.svg 960x880 8230 b2d68a34d76faa59e6e8ea983e644a5dce8cbbbedee938ec2bdf36296be4947b
diagrams/sample-00-three-ways.svg 960x880 7986 218771b7e9f945021d6d7293aca4ace3b4fec28395d8d83461e5de382bef371b
diagrams/sample-01-build-accept.svg 960x840 10678 9e6c95fbdcb962e485b2a2a866ee6ee5c00c17853ed8d2fe18c7c8d47209faa0
diagrams/sample-01-debug-connect.svg 960x990 28746 1e26ed86eff056127e7bbdeafe5ccfa963ffa1cef947307e11a148952d8db811
diagrams/sample-01-env-compare.svg 960x880 7571 6c28db1faf427b25ef1cd4920c995b6ae8cd38e381315a060de9f741b0cdeb06
diagrams/sample-01-flash-path.svg 960x880 11680 a57ee9fa3594d3ceae8acc158dd93ff19250d40914095c29209cd755cd67625a
diagrams/sample-01-flash-triage.svg 960x800 22553 3388ccce0907788efadbb65ff08021a78e2c25d627a46c5d8414800f68c43c78
diagrams/sample-01-rdp-unlock.svg 960x880 8337 68ed19a2ca697b797351a08ea7ef63f1fca3841e6002ba8406a5c0d281a3ebb4
diagrams/sample-01-swd-vectors.svg 960x980 7365 2e08712dfff9ee901d17be08e83d3496b7d34b02f3ddd73a7565d230a6291b56
diagrams/sample-02-boot-mode.svg 960x620 14370 cdcd87d572ac7b40b3d2347c8e851c51aeb4b29d9a7c82054025bc98cb456751
diagrams/sample-02-bus-matrix.svg 960x880 7375 88d9726b1d4072f7122df48bac9abe41a38e96471716166074085d5ddfbb70d4
diagrams/sample-02-clock-tree.svg 960x860 7439 41c1657ce8a1e34119ae2946ab5f10034fe5c83ef21fa50b4a1520861a1a98f2
diagrams/sample-02-flash-latency.svg 960x880 6871 6ca3bd42e32ec03d640bbf05f8f1e9ef68d33df4b03bffe66deece2b2853e55e
diagrams/sample-02-hse-fail.svg 960x720 16158 497b0d449566deabbab5c1e24d0f5f11094e20bb6372f1a6b20d4a41eb2da707
diagrams/sample-02-pll-lock.svg 960x880 10856 f2d079c74323214fd995403c50b4f9490cbdbdfffe4e004f6d26c46f30768e2f
diagrams/sample-03-current-path.svg 960x880 9948 fa7ec027eb93af7fa7a876d56d8c2baae6cf7b088a2f118e0e70cc177d37ec28
diagrams/sample-03-exti-vs-poll.svg 960x880 6618 96123571534bfde9976ea78707f7daeac7ad08ad21a12277cb5aa3c60e483ab6
diagrams/sample-03-gpio-led.svg 960x660 8264 35a7e6901de591eee1e61a095904be4e2a926c4c351c386d20b8bfda714a6abe
diagrams/sample-03-moder-map.svg 960x880 6964 79859125791b7ac0fb1a1f9bf021f1dc38f29eb7315b2b594e8b6c602942e3fa
diagrams/sample-04-exception-stack.svg 960x780 7565 bc969846347daca2048bf5b355139a73f55e436f5c5779f9ac69a92e5d458d3e
diagrams/sample-04-exti-line-map.svg 960x880 7402 cf6eac767b12695ad922f5452240230ef81f075dd9022bffe781193cb26b212b
diagrams/sample-04-exti-triage.svg 960x880 12658 5b9031358e707823f20bd002178ccfcd2e70917da6a0731b0c8d895398400999
diagrams/sample-04-priority-group.svg 960x880 6929 16a627274f441189da836bcf0c54669f73a920f87332ede79789faa6e793ca4e
diagrams/sample-04-tail-chaining.svg 960x880 7127 24e8b92d06aa15a534da40b7b2bd5083f590700adbeff14d6dc064721315ae0a
diagrams/sample-05-deadtime.svg 960x880 5215 5ea722dda19f26c821b3a5753ee7bb4ca528bf137e827d8e9886ea1fc6fc0524
diagrams/sample-05-pwm-1khz.svg 960x820 6880 48d92b03384bf3ac51e52c7d54c8a2bedd68b1a20ec405c21fbbc9287999217e
diagrams/sample-05-pwm-debug.svg 960x920 12149 90918e07f70e4c221e85dbeea40550c1a71850eba141baa1f8e9087e45610b6d
diagrams/sample-05-shadow-regs.svg 960x880 6397 7008c17b4e22262aecbf42dcaafdc2b1ddaeb5c5d9180c8f87dbcc537a928271
diagrams/sample-05-timebase-math.svg 960x880 8460 c1bcc9601c06ed9594504c4538fe3d1a38f74bf05509eb7ab0be218fc090f093
diagrams/sample-06-baud-formula.svg 960x880 5513 0ea354480d218812d1960832f683fa63862d8b7c302a270d5bde06de50eb28fe
diagrams/sample-06-baud-triage.svg 960x880 12511 39623822bf2b1e784101cebd6cf4cd7f57f5cfbebc09596b3f195ffebe578f56
diagrams/sample-06-frame-annotated.svg 960x880 10828 d41ffc3ab887c2d41b8c5bdf7ad35d17676df7bce50bc753d0d808407662112e
diagrams/sample-06-idle-dma.svg 960x840 15348 8a0b80e12adc2e955f0105a482b40b4f8c997752424ad1b542b6b77021d5448f
diagrams/sample-06-tx-rx-crossover.svg 960x880 6968 fbe536043a67ff814ac8c076f13d25647774ae61bd961d446dc6a679c2302178
diagrams/sample-06-uart-frame.svg 960x820 12513 2da90d7d086d7eabf7a11f50cbe53f3387f1b0e3ed8b97b7781ff4a41be516ee
diagrams/sample-07-i2c-addr.svg 960x920 6654 5d8aeb4df50370a3885d46d17f086e582dab7875ce914911efb247b07e8d7e5a
diagrams/sample-07-i2c-triage.svg 960x880 15555 e883d49128b6ad56b242d8f1178dc70d67f1014bfb42f958c41bf34677d54a1d
diagrams/sample-07-pullup-cap.svg 960x880 7804 8e8eeb28a80cf788b23f02b01fa301dae7454c84b618fe8fd0fbc6c71d813194
diagrams/sample-07-sr-restart.svg 960x880 8115 cceb578c44a66a2a6ee75d3af68b2f5fb94800051e2d6f6cad557766ee21a4f5
diagrams/sample-07-start-ack.svg 960x880 7267 c5d9b22469eba2d8cc91a5de66fc48a427780655e53f27f2fef1d7c3f9f9b119
diagrams/sample-08-br-table.svg 960x880 8399 db268bd78071ee714eb6b455c6054feec65d0fc8b850136f2f21291fc253ad92
diagrams/sample-08-bus-compare.svg 960x880 15494 eeab1e67083554790aaad5bf06a9f3b6be403c2e6923a83ef2f7aba1f5b0357c
diagrams/sample-08-cpha-modes.svg 960x880 18777 a8832f9b9717be139e721840e6c634b56218617fdee98684cd53f5365869290e
diagrams/sample-08-mode0-edges.svg 960x880 7399 e145fc929e00d4ad6e82cd6c9401c4728644e1e3d939792569d41ef96385d243
diagrams/sample-08-nss-multi.svg 960x880 8393 a90ab2687b329c04e2b5a42db93271ad1c32d4a30531ab0f433fd142a5381d5c
diagrams/sample-08-spi-jedec.svg 960x860 6885 717ba67544302d5517bffdbfe23deec414d5f52c49993a9eba0260fd4952fd4c
diagrams/sample-08-spi-triage.svg 960x880 15884 a8539cbccd4bcfde8df7f4ddf7ffdc1a08ac43071e1314d57ea4f912defea2bd
diagrams/sample-09-adc-sar.svg 960x860 6690 3d193aa429c4f707ea7f82cf4e6e44c2f128bc032e59d43a7e2334c5882dc65e
diagrams/sample-09-adc-triage.svg 960x880 15879 40f75ff1ab018b28a173b733bd41137e4f436a6b5d2de98123a970612f8453e8
diagrams/sample-09-sample-time.svg 960x880 6937 a991197eb83c47663c3c2c179e3fe174610b82a03b1c8d68a40463a2ba512832
diagrams/sample-09-sar-ladder.svg 960x880 8488 495d36e11ef38123ff1f730cad8db8b3dcc60ee153b012210be668c8d1bb8094
diagrams/sample-09-vref-rails.svg 960x880 5037 97bcfd3292dd4942ce00b01f0f5a109e85853a69987c582ed98ab044227ebb16
diagrams/sample-10-cndtr-ledger.svg 960x880 7411 7b7973034fd099b554ed1b548398dbe64e62b16018748ca809bea85f3791c900
diagrams/sample-10-dma-cndtr.svg 960x900 6586 6a887f553de8b9d8744527a71b0c86217ccbea32b2f4f65ff3519f519cfb92f5
diagrams/sample-10-dma-phases.svg 960x880 7442 ca77d1ea5d6fad9162c8b0cc4520fb5c5487e6c8997aa70424f355959171dcf1
diagrams/sample-10-dma-triage.svg 960x880 17093 1a2851470c10858f00b3ab55cdc7b8a15f3dcaad1f6619d39993c5df3bbf8360
diagrams/sample-10-mem2mem-vs-peri.svg 960x880 6551 68133ce5024d71b6e1b707cde7a6751ca29655f9321287f21d600e58a574017e
diagrams/sample-11-backup-domain.svg 960x880 7020 680b68d1c3231309ae293b2882feadbcadfff4725da192d4eea587e5327bb56b
diagrams/sample-11-iwdg-1s.svg 960x980 7205 226d77d6f316c4b5ce1a1580507c95b96d69a8c3a35f7601475794dc279b18eb
diagrams/sample-11-iwdg-math.svg 960x880 8432 8ba2c90d9ac51d24fe366ad12f7427ff4b3e1f440d1a8b08bd609af75f6c4279
diagrams/sample-11-rtc-triage.svg 960x880 9577 dfe343f277ccf389b6e997b8e1250bf7c6b44853055c693ee601562d0077ee8f
diagrams/sample-11-wdg-compare.svg 960x880 13910 01eb45735fbb10af2251a9c62a7d7139244a1a6f137f80f87d7706309ad86231
diagrams/sample-12-boot-compare.svg 960x880 11050 e0de5fc1765c2aefd743c265375972ecb8d5c08009db0178884d74ea5ce31441
diagrams/sample-12-flash-triage.svg 960x880 30987 2bb3a1e89b09429b86a59c3bfa3ecaaba2deebb3be5299644a4efef8d837e414
diagrams/sample-12-iap-map.svg 960x980 7487 017cfc1406a5ad4843bcdf80666eaa5636e3186fa60008f61cef514cf26f60dd
diagrams/sample-12-key-order.svg 960x880 8534 6db99921b2dfabde6ff1acf6cd0e4bac0ff05123d0558ce2004a63993c242451
diagrams/sample-12-page-erase.svg 960x880 7721 7df17f82535b7d8f4a75f1aa8558701402f7f88471131a547b8f95c3e37654bc
diagrams/sample-13-bit-quanta.svg 960x880 7797 4c760c2142e525ee23bd4905018fe65bafc57ef686eb0a226eedd3e046e8b664
diagrams/sample-13-can-bit.svg 960x980 7213 0e1da8a54f67b46946b959799eb301cf07baa63b6494fd196c00cc6514654cc8
diagrams/sample-13-can-triage.svg 960x880 9720 4e58328863259fa57f7a96e54313408ab728fb6971b631831799e1ef4482f1da
diagrams/sample-13-filter-fifo.svg 960x880 6606 2804311aa5717d55d189bd3eb2f188f85b51e82747f3ec5de79ceb1635626417
diagrams/sample-13-tec-busoff.svg 960x880 7966 77c0b03279c15a8cca5cce5f69b958bfd9dc467a89c08a194a17ebae925ed3a6
diagrams/sample-14-descriptor-map.svg 960x880 17900 a814b32a1b1f56266a1b67c7296953218982fa66319d1d82c121e702973b4bca
diagrams/sample-14-pma-map.svg 960x880 7636 aea0d7087ef6f7098294592050f891aa49640977f5a861363dc75eba5399f081
diagrams/sample-14-usb-enum.svg 960x980 7139 a6cf18d79c5d09d0257f7c8a210c9a82df4387dfac9b1239fdc1df46359bd93b
diagrams/sample-14-usbpre-48.svg 960x880 8434 4f0613fdf91f0c8e230431bf7cd198cdcce6b3a111938dc09e8be37aac6378b9
diagrams/sample-15-fromisr.svg 960x880 6908 6be5fd0850c4ee6f744d6fef75a2264d9752db4dc6bfc3dc0808afc8a4fa313a
diagrams/sample-15-rtos-prio.svg 960x960 6831 a6c5ccb5affa24af61ec70b68a8fff13810af20309f0a3cf1549a59b3b24a842
diagrams/sample-15-rtos-triage.svg 960x880 32920 532a344a2bc920e3ed45a7328839e0e2e58d3e8cee194c26c44cdaaf5b4b531f
diagrams/sample-15-task-states.svg 960x880 7968 7e869e871a969afdd2b008f4216655d687c2b8f84d23139f4595f5a7caca3ec6
diagrams/sample-16-clock-restore.svg 960x880 8622 4d5484967019fb3e4f2d1f57860f95149dd9dbc8a9cf4946f33df936f6dbeea9
diagrams/sample-16-mode-current.svg 960x880 7859 95d85b4ebe6046a6341fd085cb61a30e5835462ad10e8b7d22c9578f08ee7ac3
diagrams/sample-16-pwr-triage.svg 960x880 20343 9fecb6fb502ebcc846f9dd4b8b375ef09dae073019905c70c0cf622d60c1f4d4
diagrams/sample-16-stop-compare.svg 960x880 16112 aa1c85a1e5883623b88ca138a8fbb834c57d732c3bc25567d5d21c8f9e17b158
diagrams/sample-16-stop-wake.svg 960x980 7181 41341af8f070f2b9413b8d4fc6f3dff0d5c6afc2d767d5a36b656a1c17ef3ac4
diagrams/sample-17-cfsr-bits.svg 960x880 6912 7b5bc63434fb0b732eca18c12fb75ab6cc2794db98f906d2f7068fb276b63687
diagrams/sample-17-cfsr.svg 960x980 6762 5afb78ba8d0be29fa1bbfd8c497919296d991d9112ee2eae24f89fd9413b4d6d
diagrams/sample-17-obs-compare.svg 960x880 19906 6aa426212854d650a1fe5749c4397a5a4030c99bccc00d727ee732e098a9e847
diagrams/sample-17-perf-triage.svg 960x880 31686 5cb965c888786491459df11a425314742270c872b1933d4bbf27439bce28f433
diagrams/sample-17-swd-pins.svg 960x880 7707 78e8e20fec5a095aaa9f44ec8e1607d1287f6851e92178576cb6368c468f0d90
diagrams/sample-18-boot-triage.svg 960x960 6546 ab5be4eb7af108fbd513303dd1d1bf4ab24978018966c98fa80fcb46a9d83091
diagrams/sample-18-faq-compare.svg 960x880 18905 b20511e95158a4672284c910b050fb5dfd13802771c377dc661f83a7ebdddac8
diagrams/sample-18-hardfault-ladder.svg 960x880 7211 2a79a5afe8caa53ee7ea66b31db3a2eca97f25ac5107328bf210f1751b49d8ee
diagrams/sample-18-link-map.svg 960x880 7067 20f79b0842fefa391e31e564233d034e95580e6539f8a04fce307ea651cdd16e
diagrams/sample-18-uart-garbled.svg 960x880 7142 ebbc992a3febb34efb312517504eac232b529f0ab9aa51fdb013cf71941cf7b5
diagrams/sample-19-flash-fit.svg 960x980 6533 d2cf0662543657786e0dc4d3341cffdffe459035fb80771ffc5b3fe474e7cc42
diagrams/sample-19-milestone-triage.svg 960x880 10323 d3eac0752050e88efc49fb98ac4054455e7eb31d186b5f311e56d4e6fb0dbc91
diagrams/sample-19-pick-ladder.svg 960x880 6333 9d8d7f1f5f767fae3192d07ec1bf47a610192f6db6970ac02cf767853b546068
diagrams/sample-19-sram-budget.svg 960x880 8164 1cca5bafe536f79ba5e839b922207993a2380dba29c6f8ce8b8d721432fda29a
diagrams/sample-20-evidence-triage.svg 960x880 10080 0f4d59549ac172809e5916fce4679cfb22123fd7364c4b314f4016401cfe9b01
diagrams/sample-20-lib-compare.svg 960x880 7087 e21bc651fc7514c94cde9da5da071ca5719adbf6d1a293f1114644b9f9045d98
diagrams/sample-20-manual-names.svg 960x880 9516 5ca7540881d3df9fae17ae57c541f648b4c8dd918d4c0c921e10b458dae0c65a
diagrams/sample-21-board-compare.svg 960x880 12797 a74b12009f0249767c513dc8326a2cc2d034c92a03456a564970b463d94e256d
diagrams/sample-21-hse-load.svg 960x880 7507 2ff3e4bb0e59924566b7d528083538f7031295bb8b500726c864592f23aaad4b
diagrams/sample-21-nrst-boot0.svg 960x880 7015 a16197a0832d7a99510cb5e9382511d96cd02dd576be342619e2a79411ad7a86
diagrams/sample-21-usb-ttl.svg 960x880 6995 7001f3e4807c4b5dec42a2af17833d5a102efe73a7d872b06a6a946e2ed0b42d
diagrams/sample-21-vdd-3v3.svg 960x880 6976 460090efa2bea2ca11def9846e58208bf090576a64e53aad1e5bebd7424b855f
diagrams/sample-22-hw-gap.svg 960x880 7177 5db5fc374f08d86b74b22855cd5189cdbce885e005ae4240850d1afbe3693008
diagrams/sample-22-renode-path.svg 960x880 7269 30c05b13e89c3037a57b3ace9faf19aa170ca2186bf2733a0a27a97eb5fb2f19
diagrams/sample-22-sim-triage.svg 960x880 10046 91b5ebe5c187d49426874133fdd28b56a78352e2e72cdb6e38635a623d6c2bda
diagrams/sample-22-wokwi-scope.svg 960x880 7106 21eb65f69cae64e30c4eae14e17f9a8626cabcf40d5bfdaa1ec7410d0a23597f
diagrams/sample-23-boot0-swclk.svg 960x880 6735 3515ec4461f0300983d73a562249c8786909ea0f20d15c5487dcee82ded5d866
diagrams/sample-23-f1-copy-traps.svg 960x880 6730 6f83e88a6319dcee8145c5c50ecf4c14c431dde0b274356259f79e59edfb57e7
diagrams/sample-23-f1-g0-compare.svg 960x880 13974 1e18f381cfd9a94a4e24a124762ae91772fc0a88da36c981019dc9b53856d9ee
diagrams/sample-24-idd-jp6.svg 960x880 5953 ca9bf04627f926da5cd7960444a02955d79b782370de3f995131f6f511fe7ff7
diagrams/sample-24-mode-compare.svg 960x880 13617 e680e4f97471a3f47a241ee36ceddc54c8291daaa41d78c3e71a446706b4ac1a
diagrams/sample-24-stop2-retain.svg 960x880 6914 1779959e1e8ff84673a1ad28d3e005c12f41b80818367a9db8a42e8089791cdf
diagrams/sample-24-wake-triage.svg 960x880 10894 8f3ea058731235fd54b25d3e390aa006bc9dece35bfa0c9df30098b9adfccdcc
diagrams/sample-25-dcache-dma.svg 960x880 6847 ecfc3a59bf4d7b28bad0ea69ed714fec8b3dc49968c18038791d6d156fb21b1b
diagrams/sample-25-migrate-triage.svg 960x880 7718 e348c3b809b5cccc71d17f1b07353e78fef3191b33b581f2175bd9fdc368ff94
diagrams/sample-25-voltage-scale.svg 960x880 6444 733ea24167318cec20faf4ce57d6e328df36a0d6d2bb2950e5a10c99119fecd6
diagrams/sample-26-file-matrix.svg 960x880 7195 a2a0847e2d5b9263d695dc6073b49c3519d639ef755a0f5fee02f124f63b00e4
diagrams/sample-26-spl-hal-compare.svg 960x880 9466 66fc188f5cae5ec5d8652fb38466638eef4e3c274e5b8a2394f7dfb51c2566df
diagrams/sample-26-timeout-poll.svg 960x880 7046 3fd5cd9db286b5b34f2ce6417d83fd39b33af93112689487517ddc5721b8bc0b
diagrams/sample-27-link-triage.svg 960x880 8863 7a8daae96e3fdf54aedee566f1baf8a441a4bb24fac164df1b6225b1c5bcc622
diagrams/sample-27-rmii-checklist.svg 960x880 6292 17241eafa356d33a96119625a04338223ec26b979e10a67aca96c7317f19e71f
diagrams/sample-27-tcp-framing.svg 960x880 6879 eee4fe447091d15ad3ec28749faa9ae6ee68642fae27390fefebdf0ea7d44b4d
diagrams/sample-28-fault-triage.svg 960x880 10199 5ffe60a6bb72715c224ed684fe062284da721dfaaeda0514901bf1fe8c953c69
diagrams/sample-28-four-concepts.svg 960x880 7329 1dec27409d31d0895a54798bfd94549d7810747edb240bdd67fa98f1a294d214
diagrams/sample-28-os-compare.svg 960x880 12945 ade62396bddda3517a01bec9800ec7961005cd7247a2e78c322384eff2de4f1c
diagrams/sample-28-three-times.svg 960x880 6591 843548c0b1b0e82967d860aa62ec30c5905a88b7578a0d4ddee5920d04b01834
diagrams/sample-f-ask-before.svg 960x880 7854 0228ec7286b580dacb60722bd94ffa2ca212023e06a09c16ed5bc30dc34e36d6
diagrams/sample-f-oss-map.svg 960x880 11712 393eb0687927eb4c6301a3a5f81b0d4dda387aab6aa2f260bf13c424124aaf51
diagrams/sample-f-six-facts.svg 960x880 7704 d87feadfef30f520c12fceed884038af252a1352a4e5aab5e4f8d2d225dce80e
diagrams/simulation-model-boundary.svg 900x560 6723 365c4b15943f3a01461ec0e2ce9b0a7dbcdc199777b1b2272e04a791adeaf382
diagrams/simulator-comparison.svg 900x560 8691 264d2e8ea080e2852fe0e32c718f94a7def982efcc915e5616fe5b16c44fcc99
diagrams/single-build-contract.svg 900x560 8485 3984ce04a30ca75e25cd2659968cf984c1735cb72ee4c92c61f0759ecb87e126
diagrams/spl-ownership-boundary.svg 900x560 8419 7575a21859768a7a322837561eac717c249069fd126d27a1f4df8fa6737b2872
diagrams/tcp-byte-stream.svg 900x560 9783 f230153d1cf891c560eadcfaa35ce04d3073cf5d2c03b175bd47c894e93a8205
diagrams/watchdog-reset-evidence.svg 900x560 9405 b7882423651706cf667fd5fdfbfa9202b517d2268757f585a3eb634eccdd6fa0
illustrations/app-a-handdraw.svg 900x560 7424 05b75978bc11bd0ec9d198447038e5faf848d5e1fc188609bff19a6dfd8217a3
illustrations/app-b-handdraw.svg 900x560 10411 4565482137008aa396e1acbdc807f5195651c6305a19c3c1a5315c5088cde901
illustrations/app-c-handdraw.svg 900x560 5401 d43950347a0b55eeebf4061255113c5d9121d66ded597eeabd98eea6ac5dd05c
illustrations/app-d-handdraw.svg 900x560 6875 aa33690430198d0a4706d1c29efb6d207aadc81147d72d86addafc8040afff38
illustrations/app-e-handdraw.svg 900x560 6052 5a03e600cdf5814a8f98c9f0e8ef2271e7d8f16dd47d6d86fcc58dd4ff66781e
illustrations/app-f-handdraw.svg 900x560 6429 2f57f743444b889b10ca21f552ea657c55bf8784d95d6dad0dcbc8ed49f1efbd
illustrations/ch00-handdraw.svg 900x560 4892 690763608b44b4a8bf00499ba843af11df66a5eab6ad56d250436f8801bfc9d0
illustrations/ch00-mid-handdraw.svg 900x560 5634 0346a7588dfd31e2016cb831c27b90366c00a7631d441ad5ff29fe3dc76f1115
illustrations/ch01-handdraw.svg 900x560 7564 2762f78c2bdf7787c0fb93c39df226bb26cdb4f5fcb67ebb1364229ab2b7648e
illustrations/ch01-mid-handdraw.svg 900x560 5366 ed382975ff2698799f3f11ebfa74a1a32252966618a1f27ae0f22f439a241a7c
illustrations/ch02-handdraw.svg 900x560 6107 ca4c04775828723faf1a1134221700f6e1e5431131d9fe894a77a93fa1c1c82b
illustrations/ch02-mid-handdraw.svg 900x560 8297 ae0cca7c713899c1d12a2e8887a06901c03780564f093be1b17f38acab29918c
illustrations/ch03-handdraw.svg 900x560 8327 580d8651396694b153d02b88c3c9edd333602dc0c932f881622e6689c0b0f304
illustrations/ch03-mid-handdraw.svg 900x560 6777 34cf2d3a1f45f0a0f1a94b414b6874b3a6e2b1d44f702df096dc3112f65dba5c
illustrations/ch04-handdraw.svg 900x560 4610 37d1d7376b48112f0adffc9779832e7afdc28d08196676297dfe323234861a38
illustrations/ch04-mid-handdraw.svg 900x560 4099 eb023bca21ff24091f3359faa2683ca383932f4be7c69648569a84c8fe1cc121
illustrations/ch05-handdraw.svg 900x560 4773 982cb168e2df00ddae00f2fa69da5625ef3573334698c4f3014907180846dac5
illustrations/ch05-mid-handdraw.svg 900x560 4882 8d73882f2da0b00b0c76e8e935aa53ee68d9f68e9fa34c7b4729bd13a0be995d
illustrations/ch06-handdraw.svg 900x560 8629 eb3ad104d080d700767e8e5c4311f1aad2632c0d24371fce4bfe00ad01d3cdec
illustrations/ch06-mid-handdraw.svg 900x560 7293 4ed942eaba182f5d3fb4e8e7512eb62abcb4cdb3da0504b0ce7aabc6670efd6b
illustrations/ch07-handdraw.svg 900x560 4862 106db8f730e30248fdefbaf9cf9c22a17e8852d14f2ff7fc16593f51989e8f14
illustrations/ch07-mid-handdraw.svg 900x560 4821 d0d9a97ed471bf82bdb31dafdf07526c1d7a0ec9f686d0f0c5383f97c025690e
illustrations/ch08-handdraw.svg 900x560 7617 478be722f78f4d25ac8c976d491aeca16ff93f51b6fc912cd6a155d19d868c8e
illustrations/ch08-mid-handdraw.svg 900x560 5709 5a3cb8460644ad9134c312a087973607677126f6a881834395d473f6823694f2
illustrations/ch09-handdraw.svg 900x560 7647 975072d62ba1b96e44047ef253bad7896e10cca075d653be661f34b304e1ed87
illustrations/ch09-mid-handdraw.svg 900x560 4844 ff39ba86dfd75f912149848b2cefd0c3d0e24e8f57bde9e3ed9b669599367838
illustrations/ch10-handdraw.svg 900x560 4360 ecb58159ab3c71ef1034ce21bde4b79ff1a771dba92e03a76b5c0e0a5bb9663b
illustrations/ch10-mid-handdraw.svg 900x560 5148 2311370f7be095564cf48936a18a4cfa2b2f3f97db223cc39d80b6afa7bf9e48
illustrations/ch11-handdraw.svg 900x560 7386 6b3dff4e0ddfa3999bed370472417d9322954a568c01e642340a3c65fbadb3ca
illustrations/ch11-mid-handdraw.svg 900x560 5182 e2aa0713bda1119b97f3ee0b99c5cf32fd04fb6cfa9de0e78ac6b85310525d03
illustrations/ch12-handdraw.svg 900x560 5191 b668767313fe2638535fe3292bc390d59b4232785f3ea4c5450403230052cc24
illustrations/ch12-mid-handdraw.svg 900x560 4618 b4be855083c79e95690c88e4a4f931663d8cf3ee055b211b68b729602779a08c
illustrations/ch13-handdraw.svg 900x560 4870 1ca1c850b4bd2eaf66c80b03478bc104c91d3b85bcc742b6ada81c35bc75b7ed
illustrations/ch13-mid-handdraw.svg 900x560 8717 664d752d0149c935577d28988b205ee599fcb899c7a4edd6735cadcde5b6095f
illustrations/ch14-handdraw.svg 900x560 4577 79a5720acc05e545dbdf074195c76a0c24d3b32d1ff2cb4b2ff8251286d9857d
illustrations/ch14-mid-handdraw.svg 900x560 5550 58f7217908f5988b005fb3dc486baf0e1765f8ff46454ad0644e9f1b35b36f41
illustrations/ch15-handdraw.svg 900x560 5534 dac42641d7894f460472d8ca94d749748317037bce570e4c70a0aaaaa384150c
illustrations/ch15-mid-handdraw.svg 900x560 5021 5e4aea620f48ab0b3ddaae7b6a101b94a8fc76386330b08b90329e839cb4cd98
illustrations/ch16-handdraw.svg 900x560 6165 3d4a176113f0d5e29f38837981bd6b6ac672d9066c58e28a0a3861664f94d41c
illustrations/ch16-mid-handdraw.svg 900x560 7815 67fde27a76b64f03386bbc2fc33b6b26c9aee0aa5c722b377b0a00871410753d
illustrations/ch17-handdraw.svg 900x560 3908 65cba151b77f879d841f19badca9d522d5185134370aa61c49dce68b10e1b6ab
illustrations/ch17-mid-handdraw.svg 900x560 6290 daa6a58134ff66b5cacab3aa6c520885b100348e9a4a0e8ab232d3c977600fa3
illustrations/ch18-handdraw.svg 900x560 6684 6ae7d56e01a97c76655e3b47dce3705bf321006b2401fb75b6cfb239e752679d
illustrations/ch18-mid-handdraw.svg 900x560 7733 371b14a940ed5754ab2cf8effe7ae39809afc20978399ca4ff6cc6f18d8e47a9
illustrations/ch19-handdraw.svg 900x560 4026 238a51d3d90b336d60ad0b5d6d270d624f2f2991c2a7ea574f8ac05db65c9ee4
illustrations/ch19-mid-handdraw.svg 900x560 7734 476a849b5181865f856fb94ed3d6e0941e7c70ad7abdcc3c2b285e3d3386a8ef
illustrations/ch20-handdraw.svg 900x560 4889 f70dfa2456fc34dc180bfb8f253809d5d939f71306a65d29dfd9c2637b8c023d
illustrations/ch20-mid-handdraw.svg 900x560 6244 f43f772165b3205f33eeeefead598c778ce24156d7944fd9a515036e7d22fde8
illustrations/ch21-handdraw.svg 900x560 6562 659684e75cd4e0da00263a2dca7f771ae34b545f20800d0fa4fba78578f0cf6f
illustrations/ch21-mid-handdraw.svg 900x560 7887 f2ed3212fbce19a53c7739944b70e445399ac5c81f632d0fe18abf1149c4e534
illustrations/ch22-handdraw.svg 900x560 6311 029cc65764a9b09eed33a875c4f7c4e5f0a0007e67c1e1d34f7cb04c847cef99
illustrations/ch22-mid-handdraw.svg 900x560 9528 99d48a32603850b8e0160642985a2aec67eb887b4ae4878154457b11e3210c53
illustrations/ch23-handdraw.svg 900x560 6753 56fcf895ada916052e880503ff3d7ed741f760b816165762aafe31e4202d1b17
illustrations/ch23-mid-handdraw.svg 900x560 5923 6aa69546e74ace14092a08b90a8d4a2da967b422454e1d5c35b4d2024f4ebdb3
illustrations/ch24-handdraw.svg 900x560 6942 b81fcecb7d3380624e5b9760f0fd75051033d387ee650b0dce388f3e232fa061
illustrations/ch24-mid-handdraw.svg 900x560 8421 541020b574c9da639418df9325b199df97b633b9c8645cfab7965ba77d9262a7
illustrations/ch25-handdraw.svg 900x560 4719 8b4fb482a4270940c1a32ca49e20c0a4c7df4b67a1be56afd76601b09af35847
illustrations/ch25-mid-handdraw.svg 900x560 7344 c36bc5d40970aab60926b7dc94696c31aa9481085ac5c5b88895a3469a178ab7
illustrations/ch26-handdraw.svg 900x560 6276 a41366bc062577f07cd07d94c7cc4efb5edd56a61dbfd5336a58a94fc9e4a7ee
illustrations/ch26-mid-handdraw.svg 900x560 5843 12cbf52473a88b358982127fed45f9a67ba3b31a63609ed64e8de56722f676a7
illustrations/ch27-handdraw.svg 900x560 4568 0a399c245214680b5e7889debf36323e309af6d9f4b0ab3e53c48eba51190755
illustrations/ch27-mid-handdraw.svg 900x560 5930 a0ce44118ef9d0195eb6a6ea56d142367ac275eb42dbc4c8e9fe1b94271955a9
illustrations/ch28-handdraw.svg 900x560 4855 6ae7ea34a727496b4d95b4defcf0286d5a2bf87f0556045dcda5205f21e4b823
illustrations/ch28-mid-handdraw.svg 900x560 8108 95a26df098b5e9e958acb1dfbeb3bcc9cc6a10e69a68d119a5e3b53009d1d3be
illustrations/part-p0-handdraw.svg 900x560 8677 c589bab8908afd3e15d104fd1abb84457394ceafe1da000194f76b229b65b958
illustrations/part-p1-handdraw.svg 900x560 8064 51e467a314f6037c8b1a828a56e3362945fc3a031282db0f2202383af9935d0e
illustrations/part-p2-handdraw.svg 900x560 7702 03f742ad87a760b8240140ea38272614e9e0f13faf6ddc2faeec58492cb9a12c
illustrations/part-p3-handdraw.svg 900x560 9290 ffb9016500aacdf13e2c3d5d376b670f5438a1006b3192ca4355d705fcca24e8
illustrations/part-p4-handdraw.svg 900x560 5796 7e428592a06ec8cd42ee855642bd90945388668ab941b5f81979978f7b1dcf66
illustrations/part-p5-handdraw.svg 900x560 12963 429746577ff286fd268a8656a145ccc1562a5dcc40bc6c796923707c3899dcdb
illustrations/part-p6-handdraw.svg 900x560 4707 7b6fb10a35064337331a86fe19f6536b0bd69792e9027b649de9e95e34c7384d
""".strip().splitlines()

STATIC_ADVANCED = {
    "diagrams/firmware-stack-choice.svg",
    "diagrams/dma-buffer-ownership.svg",
    "diagrams/fault-triage-ladder.svg",
    "diagrams/first-lab-wiring.svg",
    "diagrams/first-success-gates.svg",
    "diagrams/h7-pinmux-conflicts.svg",
    "diagrams/h7-power-domains.svg",
    "diagrams/h7-revision-clock-decision.svg",
    "diagrams/h7-startup-evidence.svg",
    "diagrams/iap-acceptance-gates.svg",
    "diagrams/lowpower-current-evidence.svg",
    "diagrams/instrument-evidence-ladder.svg",
    "diagrams/manual-choice-map.svg",
    "diagrams/network-cache-ownership.svg",
    "diagrams/rtos-config-paths.svg",
    "diagrams/rtos-deadline-budget.svg",
    "diagrams/rtos-owner-task.svg",
    "diagrams/simulation-model-boundary.svg",
    "diagrams/simulator-comparison.svg",
    "diagrams/single-build-contract.svg",
    "diagrams/spl-ownership-boundary.svg",
    "diagrams/tcp-byte-stream.svg",
    "diagrams/watchdog-reset-evidence.svg",
}

SEMANTIC = {
    "#fbfaf7",
    "#f1f5f7",
    "#e5f3f8",
    "#5e6872",
    "#d7dce1",
    "#17202a",
    "#075e84",
    "#1e4d63",
    "#1b5c45",
    "#7a4e00",
    "#9a3412",
    "#8f2d2d",
    "#5b3a8c",
    "#8e2f5b",
}
PARTS = {
    "#00000055",
    "#00000066",
    "#00000088",
    "#08214a",
    "#08224a",
    "#0a0d13",
    "#0a1f5e",
    "#0a2a52",
    "#0b2c4c",
    "#0c0f16",
    "#0c2242",
    "#0d2b22",
    "#0e3b6e",
    "#0f2f8a",
    "#0f3f6b",
    "#123057",
    "#123a2e",
    "#141821",
    "#151922",
    "#153a9e",
    "#1b1f28",
    "#1d4ed8",
    "#2a3242",
    "#2b3038",
    "#39424f",
    "#4a5260",
    "#59606c",
    "#5b6472",
    "#5d6470",
    "#7aa2ff",
    "#7fd4ff",
    "#808a9a",
    "#8b98b0",
    "#8d7420",
    "#8d949e",
    "#9aa4b2",
    "#9db8ff",
    "#bcd8ff",
    "#c4b5fd",
    "#c9ced6",
    "#cfe0ff",
    "#d8b23a",
    "#dbeafe",
    "#dfe6f0",
    "#e2b23c",
    "#e7ebf0",
    "#e8f1ff",
    "#ffffff22",
}
ALLOWED = SEMANTIC | PARTS | {"#ffffff"}
BANNED = {
    "#0b1220",
    "#0e1626",
    "#111c31",
    "#16233c",
    "#243354",
    "#1a2742",
    "#e6edf3",
    "#93a4c0",
    "#64748b",
    "#22d3ee",
    "#60a5fa",
    "#34d399",
    "#fbbf24",
    "#fb923c",
    "#f87171",
    "#a78bfa",
    "#f472b6",
    "#f8fafc",
    "#c4552a",
    "#9a3d1c",
}
SOURCE_FILES = (
    "tools/svgkit.py",
    "tools/gen_sample_figures.py",
    "tools/gen_diagrams.py",
    "tools/gen_handdraw_illustrations.py",
    "tools/anim_basics.py",
    "tools/anim_gpio.py",
    "tools/anim_comm.py",
    "tools/anim_sys.py",
    "tools/gen_boards.py",
    "tools/gen_pinouts.py",
)


def load_builder():
    spec = importlib.util.spec_from_file_location("stm32_book_builder", BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder: {BUILD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text_hash(svg: str) -> str:
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", svg, flags=re.DOTALL)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


class SampleSvgCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()

    def test_sample_svg_c_contract(self) -> None:
        self.assertEqual(
            "0391297fb6f9d6616983b6f5031f10b86068d033653b610b06eb48969d130508",
            hashlib.sha256(self.builder.CSS.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            "9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd",
            text_file_hash(BOOK_DIR / "styles" / "tokens.json"),
        )
        self.assertEqual(
            "0d5a2a1f9bf631e8ba97a0ed5bf0b95b462c6057811ac751aa498994c5c92ed4",
            text_file_hash(BOOK_DIR / "styles" / "book.css"),
        )
        self.assertEqual(
            "37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd",
            text_file_hash(BOOK_DIR / "cover.svg"),
        )

        found = sorted(
            path.relative_to(REPO / "assets").as_posix()
            for path in (REPO / "assets").rglob("*.svg")
            # handraw knowledge track is a separate family with its own
            # contract (stm32-book/tests/test_handraw_track.py); see
            # BOOK_CLASSIC_CONVERGE_SPECS.md §6.1.
            if not path.relative_to(REPO / "assets").as_posix().startswith(
                "illustrations/handraw/"
            )
        )
        expected = []
        for line in ROWS:
            rel, wh, _old_size, digest = line.split()
            width, height = (int(part) for part in wh.split("x"))
            expected.append(rel)
            path = REPO / "assets" / rel
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            limit = 80 * 1024 if rel.endswith("pinout-stm32h743zi-lqfp144.svg") else 60 * 1024
            self.assertLess(len(raw), limit, rel)
            attrs = re.search(r"<svg\b([^>]*)>", text)
            self.assertIsNotNone(attrs, rel)
            self.assertEqual(str(width), re.search(r'\bwidth="(\d+)"', attrs.group(1)).group(1), rel)
            self.assertEqual(str(height), re.search(r'\bheight="(\d+)"', attrs.group(1)).group(1), rel)
            self.assertIn(f'viewBox="0 0 {width} {height}"', text, rel)
            self.assertEqual(digest, text_hash(text), rel)
            colors = {
                item.lower()
                for item in re.findall(
                    r"#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})(?![0-9A-Fa-f])",
                    text,
                )
            }
            self.assertFalse(colors - ALLOWED, (rel, sorted(colors - ALLOWED)))
            self.assertFalse(colors & BANNED, rel)
            strokes = set(re.findall(r'stroke-width="([^"]+)"', text))
            self.assertTrue(strokes <= {"1", "1.5", "2"}, (rel, strokes))
            self.assertFalse("stroke-width:" in text, rel)
            radii = set(re.findall(r'\brx="([^"]+)"', text))
            self.assertTrue(radii <= {"2", "4", "8"}, (rel, radii))
            if rel in STATIC_ADVANCED:
                self.assertNotIn("<animate", text, rel)
                self.assertNotIn("@keyframes", text, rel)
                self.assertNotIn("animation:", text, rel)
                self.assertNotIn("矢量动画", text, rel)
                self.assertIn("自绘矢量图", text, rel)
            elif rel.startswith("animations/") and Path(rel).name.startswith("sample-"):
                # B5+ playable mechanism demos: CSS keyframes allowed; first frame PDF-readable.
                self.assertNotIn("<animate", text, rel)
                self.assertIn("@keyframes", text, rel)
                self.assertIn("自绘矢量动画", text, rel)
            elif Path(rel).name.startswith("sample-"):
                self.assertNotIn("<animate", text, rel)
                self.assertNotIn("@keyframes", text, rel)
                self.assertNotIn("animation:", text, rel)
                self.assertNotIn("矢量动画", text, rel)
                self.assertIn("自绘", text, rel)
            else:
                self.assertIn("自绘矢量动画", text, rel)
        self.assertEqual(expected, found)
        self.assertEqual(324, len(found))

        i2c = (REPO / "assets" / "animations" / "i2c-transaction.svg").read_text(encoding="utf-8")
        self.assertNotIn("<style", i2c)
        self.assertNotIn("<animate", i2c)

        gifs = sorted((REPO / "assets" / "gif").glob("*.gif"), key=lambda path: path.name)
        self.assertEqual(48, len(gifs))
        listing = "".join(
            f"{path.name} {hashlib.sha256(path.read_bytes()).hexdigest()}\n"
            for path in gifs
        )
        self.assertEqual(
            "492ddd36e5046add3e522cfc136d264f86ce66361580110e851746d093afb68a",
            hashlib.sha256(listing.encode("utf-8")).hexdigest(),
        )

        svgkit = (REPO / "tools" / "svgkit.py").read_text(encoding="utf-8")
        self.assertIn('BG = "#fbfaf7"', svgkit)
        self.assertIn('CYAN = "#075e84"', svgkit)
        self.assertNotIn("WHITE", svgkit)
        self.assertNotIn("#0b1220", svgkit)
        self.assertNotIn("#22d3ee", svgkit)
        self.assertIn("PingFang SC", svgkit)
        self.assertIn("Hiragino Sans GB", svgkit)

        for rel in SOURCE_FILES:
            source = (REPO / rel).read_text(encoding="utf-8")
            self.assertNotIn('fill="#0b1220"', source, rel)
            self.assertNotIn("T.WHITE", source, rel)
        sample_src = (REPO / "tools" / "gen_sample_figures.py").read_text(encoding="utf-8")
        self.assertNotIn("rx=10", sample_src)
        self.assertNotIn("rx=6", sample_src)


if __name__ == "__main__":
    unittest.main()
