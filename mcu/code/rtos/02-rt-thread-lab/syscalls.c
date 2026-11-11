/**
 * syscalls.c —— newlib 最小系统调用桩
 *
 * 嵌入式上没有操作系统，所以 libc 的 printf/snprintf 要落地，
 * 必须有人实现这几个"系统调用"。这就是教科书里 retarget 的全部内容：
 *
 *   _write → 串口（本工程唯一真正的输出）
 *   _sbrk  → 链接脚本给的 end 到栈底之间的内存（libc 内部才用）
 *   其余   → 返回"不支持"或直接停住，绝不能静默成功
 *
 * 有了这 30 行，vTaskList()（内部用 snprintf）就能直接工作。
 */

#include <sys/stat.h>
#include <stdint.h>
#include <errno.h>

extern void console_putc(char c);   /* main.c 里实现，往 USART1 吐字节 */

/* printf/snprintf 的最终出口 */
int _write(int fd, const char *buf, int len)
{
    (void)fd;
    for (int i = 0; i < len; i++) {
        if (buf[i] == '\n') {
            console_putc('\r');
        }
        console_putc(buf[i]);
    }
    return len;
}

/* libc 可能要堆：用链接脚本里的 end 到栈之间的内存 */
extern char end;                    /* 链接脚本 PROVIDE(end = .) */
extern char _estack;                /* 栈顶 */

void *_sbrk(int incr)
{
    static char *heap_end = NULL;
    char *prev;

    if (heap_end == NULL) {
        heap_end = &end;
    }
    prev = heap_end;

    /* 栈和堆之间留 512 字节缓冲区，撞上就让 malloc 失败而不是踩栈 */
    if (heap_end + incr > (&_estack - 512)) {
        errno = ENOMEM;
        return (void *)-1;
    }
    heap_end += incr;
    return prev;
}

int _read(int fd, char *buf, int len)
{
    (void)fd; (void)buf; (void)len;
    return 0;                        /* 没有输入设备 */
}

int _close(int fd) { (void)fd; return -1; }
int _fstat(int fd, struct stat *st) { (void)fd; st->st_mode = S_IFCHR; return 0; }
int _isatty(int fd) { (void)fd; return 1; }
int _lseek(int fd, int off, int whence) { (void)fd; (void)off; (void)whence; return 0; }
int _kill(int pid, int sig) { (void)pid; (void)sig; errno = EINVAL; return -1; }
int _getpid(void) { return 1; }

void _exit(int code)
{
    (void)code;
    for (;;) { }                     /* 裸机上没有"退出"，停住等看门狗/调试器 */
}