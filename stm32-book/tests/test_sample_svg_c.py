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
animations/adc-sar.svg 900x620 19409 ebd3127f7efde5d3c25f5a82dea6ae36eaff2a4c3a87c698f95f0d329a0ca807
animations/boot-sequence.svg 900x620 14058 d6d1baa08f2d9763ef5971f4701775db3905d34a7d6998310b127dd21beaddfc
animations/can-arbitration.svg 900x620 23362 6a68426929c8ad0f4046b091ae4be6db894eba2e4125f1e03c41c695167a3176
animations/clock-tree.svg 900x620 10921 c0e07c5c01bffae9769331541bdf87dcfc4ea61e3b4081b6f72834b476fbed08
animations/debug-swo.svg 900x620 12545 e44f13c22225782401c9b3d44f376781297c0103040118786626621476a6ffdd
animations/dma-circular.svg 900x620 16488 7deb7de9dc81e1a01c1c2e01827c131661f5b6d45bb5c2fb1d0473e126041fd1
animations/flash-iap.svg 900x620 12795 55ad4b20f25654a8bb6a705303a99d5fb513f5b125b70a4545278f84d63ad0cb
animations/freertos-scheduler.svg 900x620 15775 fe1bebd106b7c825a5d815edc67842821a8298e6e98036153641ca928c098bb3
animations/g0-boot-swd.svg 900x620 12398 e9121dfb6e5290afd5d192048fa7d7409a821c7651538c80bde3237df535155f
animations/gpio-blink.svg 900x620 14249 811377a9c3b65dd99cbeb8a1ff720b0e4e6410bc852726ac98f9aa20619175ea
animations/gpio-input-interrupt.svg 900x620 13740 4b97aeb339eb046f0091312b6caf918b1acdc176cc72e4295cc7c116792c6697
animations/h7-clock-chain.svg 900x620 11808 4edcb50a1871b7dd97c5a86685f43b5884c92aec162c53aa478f519394dc2068
animations/i2c-transaction.svg 900x620 17483 e5c5b2aca2aae67cc607e3eb929cc0f20c184deceb8815f32a9d4e96f4bef55a
animations/iwdg-window.svg 900x620 10675 324f8c83215265a9e4b9c256552019165c14adb914c3fc9189f054f264751444
animations/l4-stop2-evidence.svg 900x620 14214 04228f72309b692ff19fdbccce10fe8a7fc1a1030af9f83bba0307fc7896bd1e
animations/lowpower-wakeup.svg 900x620 10766 7a5fe86d6e1a29c7f8e00d177f0ec928c85f7405e8427e8f27209720cc0a22b6
animations/memory-map.svg 900x620 7846 82e9be18ac7ecbe388e478b995ef9bcf8e876a2373406565469fda41e911b11f
animations/network-online-state.svg 900x620 12028 b411a492adbc81a722ace75d62461b5b21a8c97a364d0f253fb43e1b09df8fdb
animations/network-packet-journey.svg 900x620 18648 0081c4c6270e94527deba9ea9365811c22de28130ee343d8df68797eb36f1016
animations/nvic-interrupt-flow.svg 900x620 12972 07a38a7e7d4b430809683b2beb00f98b3cac0a17fc45bb1a5d066d20c22c9dc4
animations/rtos-startup-gates.svg 900x620 14083 8e65b6e47917be3fdd79f4b51834520927b144caa4ed12b6d392e21823464b3b
animations/rtos-system-layers.svg 900x620 13996 1a44f6f16dcc08a20467d946a35a22ef968582f37faf99b5b74f5107deaf31e9
animations/simulation-acceptance-gates.svg 900x620 10660 c0316576a9b8a6c45011d4a1fce3f884228ffa2a0788561d983b43227aa9e146
animations/spi-transfer.svg 900x620 18861 579ddd86d159809dc4c667a0bf1faf652c1c0538d4d155f6f7187896df7a3968
animations/spl-init-pipeline.svg 900x620 11903 d1ebfca0e4b6e9cbbda864bf9c82f217976ad6b8e16bee53e36059b6d6e8885c
animations/timer-modes.svg 900x620 11712 c8a1e34469293d5f4a02a5703271bcf62fc4e9f2f1e89429dbcaa02b56ebeabf
animations/timer-pwm.svg 900x620 10046 54833bf0841b1569cb993934699473b2ee4d2f0ed56b858a4fb9b5855bb8532f
animations/toolchain-flow.svg 900x620 15176 e131ad994e16c099c15d4d941c0e7aade4865c53c912248a73590e939645e0bd
animations/uart-frame.svg 900x620 18533 a696fc8932d337f1b22dacef54ecfe01dd37aa963b41d67111c584122f6b3400
animations/uart-idle-dma.svg 900x620 15121 8e6bf1c20266575d08c94817d1b467bfd7ce11fc9c79adf666aba4eaabab914d
animations/usb-enumeration.svg 900x620 16705 ccf597d223d3d29cf8f5c3cbc47709d384453048753e4725cad655e84e7b0a1d
boards/blackpill-stm32f411ce.svg 900x620 32264 511d86c80d8862e78be2a0c7e6ca7e24e1db11d30ea66d47b3b2f1e8cdec0494
boards/bluepill-stm32f103c8t6.svg 900x620 35647 272634dc07da80d8c5d7e6471d9778310292318aace55acbecfcd92a8d9d4c25
boards/f103zet6-dev.svg 900x620 26509 8d52a625b72cef5f53be80091fc870d3bcf9537b0c178c5aa4ebfcb810ded612
boards/f4-discovery.svg 900x620 26524 d0d4d756b30de2d1a11a43bd78abd0f733dcf2696cc88f708de8cde63cfe659f
boards/nucleo-f411re.svg 900x620 21385 434fa875affbab6a0d987df16919de7b6cfaf88c3703da29593bef68b5006c8b
boards/peripheral-wiring.svg 900x620 13970 a5517214a0d7efcb8721fa41c8fee6224a7deca98f193bf39147ccc3f36fd166
boards/pinout-bluepill.svg 900x620 35176 4de478b58c8d278166311b99311183121ccf1ecb38a50c99450b35e60893cabd
boards/pinout-stm32g071rb-lqfp64.svg 620x750 34523 7ccc8b702e15d0473bfc1d4c956397dfbb5bd50363d4e762bd100c794d1d2193
boards/pinout-stm32h743zi-lqfp144.svg 840x970 75786 4d71ec5cab732513073bac6721ae4c688a36f18ab11fcae4b5e6e927433b7a96
boards/pinout-stm32l476rg-lqfp64.svg 620x750 34508 a5a8468d7b087956a4635ac7c88412f1e7920570c53e388e0a10a44fbe5f8adf
diagrams/classic-03-bitband.svg 960x660 10896 802dd2de3ba9b21add09a8e7cb6e459ebca21b1ed2722d654666bdc922cedaf0
diagrams/classic-03-debounce.svg 960x660 11113 6bd1b7b8c6f2e744830ccdb5aefe0f3276d291a0fe5c81f5bf0186030c8798d7
diagrams/classic-03-ft-evidence.svg 960x660 8220 f1697e2aba1a0b826e98324eed0bfc1ef975e36446d30ae130393673c6ff76b9
diagrams/classic-03-init-code.svg 960x660 9057 b1a622b9fc6d34d668cb3be4bd0caa19f50179f5fdcc7c6c0e77b20fa2f39f3a
diagrams/classic-03-open-drain.svg 960x660 14300 f82fdd1683523576bcb37ba9f77660ae4fb10c8643487d10dac5444a7c52ec74
diagrams/classic-03-pa0-pa1-wiring.svg 960x660 11036 207a23c9c085d9aac37b710034a5a1101d3d4a4e9cc85e55614af2e56bb16070
diagrams/classic-03-pc13-evidence.svg 960x660 10605 687969113f8f812f901bdfeec8d6751fb8f3feda884364f8b646c0580babf5d2
diagrams/classic-03-polling.svg 960x660 9712 a126b851e13cfdf196d89eecc8dadd2fdc7ce9fe17aeac87d0d4d3c5dbfab65f
diagrams/classic-03-register-map.svg 960x660 11947 c9f7f9646798ee2cc43bf0b8c021efbef8d9b3e8bfdff5f29b5adf6ce5cadd1c
diagrams/classic-03-remap.svg 960x660 9069 59d6d6a9a552b797394cc67593739fb944ecd8609febd7c4c290bee85ccd05d1
diagrams/classic-03-write-methods.svg 960x660 10438 9bbc68ad681faeadd134ef89c10528eea8378b16f240397c437971b55850c960
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
diagrams/interrupt-priority.svg 900x560 11877 7f3d8b282ed7342a56b598694137c3091ca4bd4a10acc73cd5a651a9b0c7fe05
diagrams/l4-idd-bench.svg 900x560 8736 e7fb7cbbf8f803d0f622784493ecb16f0596565606f77ef6f757d3559900d66f
diagrams/layers-hal-ll-reg.svg 900x560 10401 60098b25b368c2f6acefb4e9a3152f816506cae44e68b2fb8ffbf0878c049f78
diagrams/lowpower-current-evidence.svg 900x560 6553 b179af76c293ac0d9ba059570b55a2b83bdc82f077d74387c85581f25765d3e6
diagrams/manual-choice-map.svg 900x560 9687 75a6977234623a1b9e8edbd6129863f67cd9ab3ad4a4eeec7e55abe96fece3e9
diagrams/network-cache-ownership.svg 900x560 10014 5e743984bd7bf6e68f539020ac23d5a7498e89ac1788e6a3d1245c47b94daf85
diagrams/network-debug-ladder.svg 900x560 11278 a1405054a5ba593090ad0bc6fdb104a5c8e513dd9695bd35767867faeeaec2e8
diagrams/peripheral-bus.svg 900x560 14071 80d659d44758f54a352b8447fb4a49e6fa880a47cb981bc487c1d69aaa6ae2f6
diagrams/project-structure.svg 900x560 13014 53f68cd4e58288a346e7cd09867724a75daa564e3b527a46a67627250def2acf
diagrams/rtos-config-paths.svg 900x560 12512 02d7b84ba4c8fe73dcf6ea89937dfc0ebb995f7d782164fa36ba8748e708d80c
diagrams/rtos-deadline-budget.svg 900x560 8875 eec759b57c52c884ef1d126b8a0a139cb9e450dbfa561a5cb0af0467e6cb561f
diagrams/rtos-owner-task.svg 900x560 8947 0023f1657fb272cc36e19156764f8a6a4cf5a6417bff26ef764a979f7b4d32eb
diagrams/sample-00-accept-gate.svg 960x860 9596 487806482cb3425ed05fece88056fc3a1c1cf4fe38ed27c4815b5446be92129d
diagrams/sample-00-boot-state.svg 960x620 7103 41eff7ecd092c9f1d0e41629b4b87f337ea9d27e4b63f3ddda1d03e96c3eb3b1
diagrams/sample-00-boot-triage.svg 960x970 10066 a9459d49838934d93ceb23b754cd24d98204533b91876828b19371d1ec0707dc
diagrams/sample-00-learn-loop.svg 960x860 12078 f6e3cb6fb26e7495c348d26bd11143a1c181c3efe45e67975bea9bc970d6a728
diagrams/sample-01-build-accept.svg 960x840 10676 9e6c95fbdcb962e485b2a2a866ee6ee5c00c17853ed8d2fe18c7c8d47209faa0
diagrams/sample-01-debug-connect.svg 960x990 10075 bea64b761d5fd1c18356a9ec5ec15b3a7ef8c73712440693af25c7d64ab23196
diagrams/sample-01-flash-path.svg 960x880 11620 a57ee9fa3594d3ceae8acc158dd93ff19250d40914095c29209cd755cd67625a
diagrams/sample-01-flash-triage.svg 960x920 8490 13384461f93ab19f757290a55ed373c02d752386c25101432395228931f697ac
diagrams/sample-01-swd-vectors.svg 960x980 7328 2e08712dfff9ee901d17be08e83d3496b7d34b02f3ddd73a7565d230a6291b56
diagrams/sample-02-boot-mode.svg 960x920 8904 b4aa807c16c1b7732f624f8b68f3873879d2948e1c934c6c395cbacdd3410693
diagrams/sample-02-clock-tree.svg 960x860 7402 41c1657ce8a1e34119ae2946ab5f10034fe5c83ef21fa50b4a1520861a1a98f2
diagrams/sample-02-hse-fail.svg 960x900 8754 47cb6b3456c1afbccb2362ffded498b6f451ca3b0236489210451bcba8d06d93
diagrams/sample-03-gpio-led.svg 960x660 8220 35a7e6901de591eee1e61a095904be4e2a926c4c351c386d20b8bfda714a6abe
diagrams/sample-04-exception-stack.svg 960x780 7528 bc969846347daca2048bf5b355139a73f55e436f5c5779f9ac69a92e5d458d3e
diagrams/sample-04-exti-triage.svg 960x880 12658 5b9031358e707823f20bd002178ccfcd2e70917da6a0731b0c8d895398400999
diagrams/sample-05-pwm-1khz.svg 960x820 6845 48d92b03384bf3ac51e52c7d54c8a2bedd68b1a20ec405c21fbbc9287999217e
diagrams/sample-05-pwm-debug.svg 960x920 12147 90918e07f70e4c221e85dbeea40550c1a71850eba141baa1f8e9087e45610b6d
diagrams/sample-06-baud-triage.svg 960x880 9012 9eaf42b59083f53333adf8bef5fce9ac78536d469a0b29fbc77eb793975e73f1
diagrams/sample-06-idle-dma.svg 960x840 15348 8a0b80e12adc2e955f0105a482b40b4f8c997752424ad1b542b6b77021d5448f
diagrams/sample-06-uart-frame.svg 960x820 12448 2da90d7d086d7eabf7a11f50cbe53f3387f1b0e3ed8b97b7781ff4a41be516ee
diagrams/sample-07-i2c-addr.svg 960x920 6620 5d8aeb4df50370a3885d46d17f086e582dab7875ce914911efb247b07e8d7e5a
diagrams/sample-07-i2c-triage.svg 960x880 15555 e883d49128b6ad56b242d8f1178dc70d67f1014bfb42f958c41bf34677d54a1d
diagrams/sample-08-cpha-modes.svg 960x880 18777 a8832f9b9717be139e721840e6c634b56218617fdee98684cd53f5365869290e
diagrams/sample-08-spi-jedec.svg 960x860 6850 717ba67544302d5517bffdbfe23deec414d5f52c49993a9eba0260fd4952fd4c
diagrams/sample-08-spi-triage.svg 960x880 9199 b40d75cbc76bf1d00c1bcf6059a6a9acb05148a6a2465e03131bd1dfbbd68be5
diagrams/sample-09-adc-sar.svg 960x860 6656 3d193aa429c4f707ea7f82cf4e6e44c2f128bc032e59d43a7e2334c5882dc65e
diagrams/sample-09-adc-triage.svg 960x880 11279 3f34454191defda44ef0b893ae5d1584b2ce13c9baa2ade07c54bd31089c8dbe
diagrams/sample-10-dma-cndtr.svg 960x900 6552 6a887f553de8b9d8744527a71b0c86217ccbea32b2f4f65ff3519f519cfb92f5
diagrams/sample-10-dma-triage.svg 960x880 10284 1c7e9f8d07636051dfe5a5d33ddbaa9634b8d9c4968e729c141748fb93e5262d
diagrams/sample-11-iwdg-1s.svg 960x980 7169 226d77d6f316c4b5ce1a1580507c95b96d69a8c3a35f7601475794dc279b18eb
diagrams/sample-12-iap-map.svg 960x980 7450 017cfc1406a5ad4843bcdf80666eaa5636e3186fa60008f61cef514cf26f60dd
diagrams/sample-13-can-bit.svg 960x980 7175 0e1da8a54f67b46946b959799eb301cf07baa63b6494fd196c00cc6514654cc8
diagrams/sample-14-usb-enum.svg 960x980 7101 a6cf18d79c5d09d0257f7c8a210c9a82df4387dfac9b1239fdc1df46359bd93b
diagrams/sample-15-rtos-prio.svg 960x960 6794 a6c5ccb5affa24af61ec70b68a8fff13810af20309f0a3cf1549a59b3b24a842
diagrams/sample-16-stop-wake.svg 960x980 7143 41341af8f070f2b9413b8d4fc6f3dff0d5c6afc2d767d5a36b656a1c17ef3ac4
diagrams/sample-17-cfsr.svg 960x980 6727 5afb78ba8d0be29fa1bbfd8c497919296d991d9112ee2eae24f89fd9413b4d6d
diagrams/sample-18-boot-triage.svg 960x960 6512 ab5be4eb7af108fbd513303dd1d1bf4ab24978018966c98fa80fcb46a9d83091
diagrams/sample-19-flash-fit.svg 960x980 6499 d2cf0662543657786e0dc4d3341cffdffe459035fb80771ffc5b3fe474e7cc42
diagrams/simulation-model-boundary.svg 900x560 6723 365c4b15943f3a01461ec0e2ce9b0a7dbcdc199777b1b2272e04a791adeaf382
diagrams/simulator-comparison.svg 900x560 8691 264d2e8ea080e2852fe0e32c718f94a7def982efcc915e5616fe5b16c44fcc99
diagrams/single-build-contract.svg 900x560 8485 3984ce04a30ca75e25cd2659968cf984c1735cb72ee4c92c61f0759ecb87e126
diagrams/spl-ownership-boundary.svg 900x560 8419 7575a21859768a7a322837561eac717c249069fd126d27a1f4df8fa6737b2872
diagrams/tcp-byte-stream.svg 900x560 9783 f230153d1cf891c560eadcfaa35ce04d3073cf5d2c03b175bd47c894e93a8205
diagrams/watchdog-reset-evidence.svg 900x560 9405 b7882423651706cf667fd5fdfbfa9202b517d2268757f585a3eb634eccdd6fa0
illustrations/app-a-handdraw.svg 900x560 7361 05b75978bc11bd0ec9d198447038e5faf848d5e1fc188609bff19a6dfd8217a3
illustrations/app-b-handdraw.svg 900x560 10340 4565482137008aa396e1acbdc807f5195651c6305a19c3c1a5315c5088cde901
illustrations/app-c-handdraw.svg 900x560 5353 d43950347a0b55eeebf4061255113c5d9121d66ded597eeabd98eea6ac5dd05c
illustrations/app-d-handdraw.svg 900x560 6815 aa33690430198d0a4706d1c29efb6d207aadc81147d72d86addafc8040afff38
illustrations/app-e-handdraw.svg 900x560 6003 5a03e600cdf5814a8f98c9f0e8ef2271e7d8f16dd47d6d86fcc58dd4ff66781e
illustrations/app-f-handdraw.svg 900x560 6375 2f57f743444b889b10ca21f552ea657c55bf8784d95d6dad0dcbc8ed49f1efbd
illustrations/ch00-handdraw.svg 900x560 4892 690763608b44b4a8bf00499ba843af11df66a5eab6ad56d250436f8801bfc9d0
illustrations/ch00-mid-handdraw.svg 900x560 5586 0346a7588dfd31e2016cb831c27b90366c00a7631d441ad5ff29fe3dc76f1115
illustrations/ch01-handdraw.svg 900x560 7564 2762f78c2bdf7787c0fb93c39df226bb26cdb4f5fcb67ebb1364229ab2b7648e
illustrations/ch01-mid-handdraw.svg 900x560 5318 ed382975ff2698799f3f11ebfa74a1a32252966618a1f27ae0f22f439a241a7c
illustrations/ch02-handdraw.svg 900x560 6107 ca4c04775828723faf1a1134221700f6e1e5431131d9fe894a77a93fa1c1c82b
illustrations/ch02-mid-handdraw.svg 900x560 8233 ae0cca7c713899c1d12a2e8887a06901c03780564f093be1b17f38acab29918c
illustrations/ch03-handdraw.svg 900x560 8263 580d8651396694b153d02b88c3c9edd333602dc0c932f881622e6689c0b0f304
illustrations/ch03-mid-handdraw.svg 900x560 6720 34cf2d3a1f45f0a0f1a94b414b6874b3a6e2b1d44f702df096dc3112f65dba5c
illustrations/ch04-handdraw.svg 900x560 4610 37d1d7376b48112f0adffc9779832e7afdc28d08196676297dfe323234861a38
illustrations/ch04-mid-handdraw.svg 900x560 4062 eb023bca21ff24091f3359faa2683ca383932f4be7c69648569a84c8fe1cc121
illustrations/ch05-handdraw.svg 900x560 4773 982cb168e2df00ddae00f2fa69da5625ef3573334698c4f3014907180846dac5
illustrations/ch05-mid-handdraw.svg 900x560 4840 8d73882f2da0b00b0c76e8e935aa53ee68d9f68e9fa34c7b4729bd13a0be995d
illustrations/ch06-handdraw.svg 900x560 8629 eb3ad104d080d700767e8e5c4311f1aad2632c0d24371fce4bfe00ad01d3cdec
illustrations/ch06-mid-handdraw.svg 900x560 7234 4ed942eaba182f5d3fb4e8e7512eb62abcb4cdb3da0504b0ce7aabc6670efd6b
illustrations/ch07-handdraw.svg 900x560 4862 106db8f730e30248fdefbaf9cf9c22a17e8852d14f2ff7fc16593f51989e8f14
illustrations/ch07-mid-handdraw.svg 900x560 4780 d0d9a97ed471bf82bdb31dafdf07526c1d7a0ec9f686d0f0c5383f97c025690e
illustrations/ch08-handdraw.svg 900x560 7617 478be722f78f4d25ac8c976d491aeca16ff93f51b6fc912cd6a155d19d868c8e
illustrations/ch08-mid-handdraw.svg 900x560 5662 5a3cb8460644ad9134c312a087973607677126f6a881834395d473f6823694f2
illustrations/ch09-handdraw.svg 900x560 7647 975072d62ba1b96e44047ef253bad7896e10cca075d653be661f34b304e1ed87
illustrations/ch09-mid-handdraw.svg 900x560 4803 ff39ba86dfd75f912149848b2cefd0c3d0e24e8f57bde9e3ed9b669599367838
illustrations/ch10-handdraw.svg 900x560 4360 ecb58159ab3c71ef1034ce21bde4b79ff1a771dba92e03a76b5c0e0a5bb9663b
illustrations/ch10-mid-handdraw.svg 900x560 5102 2311370f7be095564cf48936a18a4cfa2b2f3f97db223cc39d80b6afa7bf9e48
illustrations/ch11-handdraw.svg 900x560 7386 6b3dff4e0ddfa3999bed370472417d9322954a568c01e642340a3c65fbadb3ca
illustrations/ch11-mid-handdraw.svg 900x560 5139 e2aa0713bda1119b97f3ee0b99c5cf32fd04fb6cfa9de0e78ac6b85310525d03
illustrations/ch12-handdraw.svg 900x560 5191 b668767313fe2638535fe3292bc390d59b4232785f3ea4c5450403230052cc24
illustrations/ch12-mid-handdraw.svg 900x560 4579 b4be855083c79e95690c88e4a4f931663d8cf3ee055b211b68b729602779a08c
illustrations/ch13-handdraw.svg 900x560 4870 1ca1c850b4bd2eaf66c80b03478bc104c91d3b85bcc742b6ada81c35bc75b7ed
illustrations/ch13-mid-handdraw.svg 900x560 8648 664d752d0149c935577d28988b205ee599fcb899c7a4edd6735cadcde5b6095f
illustrations/ch14-handdraw.svg 900x560 4577 79a5720acc05e545dbdf074195c76a0c24d3b32d1ff2cb4b2ff8251286d9857d
illustrations/ch14-mid-handdraw.svg 900x560 5504 58f7217908f5988b005fb3dc486baf0e1765f8ff46454ad0644e9f1b35b36f41
illustrations/ch15-handdraw.svg 900x560 5534 dac42641d7894f460472d8ca94d749748317037bce570e4c70a0aaaaa384150c
illustrations/ch15-mid-handdraw.svg 900x560 4978 5e4aea620f48ab0b3ddaae7b6a101b94a8fc76386330b08b90329e839cb4cd98
illustrations/ch16-handdraw.svg 900x560 6165 3d4a176113f0d5e29f38837981bd6b6ac672d9066c58e28a0a3861664f94d41c
illustrations/ch16-mid-handdraw.svg 900x560 7750 67fde27a76b64f03386bbc2fc33b6b26c9aee0aa5c722b377b0a00871410753d
illustrations/ch17-handdraw.svg 900x560 3908 65cba151b77f879d841f19badca9d522d5185134370aa61c49dce68b10e1b6ab
illustrations/ch17-mid-handdraw.svg 900x560 6235 daa6a58134ff66b5cacab3aa6c520885b100348e9a4a0e8ab232d3c977600fa3
illustrations/ch18-handdraw.svg 900x560 6684 6ae7d56e01a97c76655e3b47dce3705bf321006b2401fb75b6cfb239e752679d
illustrations/ch18-mid-handdraw.svg 900x560 7670 371b14a940ed5754ab2cf8effe7ae39809afc20978399ca4ff6cc6f18d8e47a9
illustrations/ch19-handdraw.svg 900x560 4026 238a51d3d90b336d60ad0b5d6d270d624f2f2991c2a7ea574f8ac05db65c9ee4
illustrations/ch19-mid-handdraw.svg 900x560 7673 476a849b5181865f856fb94ed3d6e0941e7c70ad7abdcc3c2b285e3d3386a8ef
illustrations/ch20-handdraw.svg 900x560 4889 f70dfa2456fc34dc180bfb8f253809d5d939f71306a65d29dfd9c2637b8c023d
illustrations/ch20-mid-handdraw.svg 900x560 6190 f43f772165b3205f33eeeefead598c778ce24156d7944fd9a515036e7d22fde8
illustrations/ch21-handdraw.svg 900x560 6562 659684e75cd4e0da00263a2dca7f771ae34b545f20800d0fa4fba78578f0cf6f
illustrations/ch21-mid-handdraw.svg 900x560 7819 f2ed3212fbce19a53c7739944b70e445399ac5c81f632d0fe18abf1149c4e534
illustrations/ch22-handdraw.svg 900x560 6311 029cc65764a9b09eed33a875c4f7c4e5f0a0007e67c1e1d34f7cb04c847cef99
illustrations/ch22-mid-handdraw.svg 900x560 9449 99d48a32603850b8e0160642985a2aec67eb887b4ae4878154457b11e3210c53
illustrations/ch23-handdraw.svg 900x560 6753 56fcf895ada916052e880503ff3d7ed741f760b816165762aafe31e4202d1b17
illustrations/ch23-mid-handdraw.svg 900x560 5872 6aa69546e74ace14092a08b90a8d4a2da967b422454e1d5c35b4d2024f4ebdb3
illustrations/ch24-handdraw.svg 900x560 6942 b81fcecb7d3380624e5b9760f0fd75051033d387ee650b0dce388f3e232fa061
illustrations/ch24-mid-handdraw.svg 900x560 8351 541020b574c9da639418df9325b199df97b633b9c8645cfab7965ba77d9262a7
illustrations/ch25-handdraw.svg 900x560 4719 8b4fb482a4270940c1a32ca49e20c0a4c7df4b67a1be56afd76601b09af35847
illustrations/ch25-mid-handdraw.svg 900x560 7291 c36bc5d40970aab60926b7dc94696c31aa9481085ac5c5b88895a3469a178ab7
illustrations/ch26-handdraw.svg 900x560 6276 a41366bc062577f07cd07d94c7cc4efb5edd56a61dbfd5336a58a94fc9e4a7ee
illustrations/ch26-mid-handdraw.svg 900x560 5793 12cbf52473a88b358982127fed45f9a67ba3b31a63609ed64e8de56722f676a7
illustrations/ch27-handdraw.svg 900x560 4568 0a399c245214680b5e7889debf36323e309af6d9f4b0ab3e53c48eba51190755
illustrations/ch27-mid-handdraw.svg 900x560 5883 a0ce44118ef9d0195eb6a6ea56d142367ac275eb42dbc4c8e9fe1b94271955a9
illustrations/ch28-handdraw.svg 900x560 4855 6ae7ea34a727496b4d95b4defcf0286d5a2bf87f0556045dcda5205f21e4b823
illustrations/ch28-mid-handdraw.svg 900x560 8042 95a26df098b5e9e958acb1dfbeb3bcc9cc6a10e69a68d119a5e3b53009d1d3be
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
            elif Path(rel).name.startswith("sample-"):
                self.assertNotIn("<animate", text, rel)
                self.assertNotIn("@keyframes", text, rel)
                self.assertNotIn("animation:", text, rel)
                self.assertNotIn("矢量动画", text, rel)
                self.assertIn("自绘", text, rel)
            else:
                self.assertIn("自绘矢量动画", text, rel)
        self.assertEqual(expected, found)
        self.assertEqual(190, len(found))

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
            "9f4d7b2c46578f975436d92901b30c8e4588b31e2df337785b9ccc0e74508c51",
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
