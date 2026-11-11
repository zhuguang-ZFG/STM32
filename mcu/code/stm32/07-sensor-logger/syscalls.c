/* These applications use FreeRTOS heap_4, not libc allocation or stdout. */
#include <errno.h>
#include <sys/stat.h>
int _write(int f,const char *p,int n){(void)f;(void)p;(void)n;errno=ENOSYS;return -1;}
void *_sbrk(int n){(void)n;errno=ENOMEM;return (void *)-1;}
int _read(int f,char *p,int n){(void)f;(void)p;(void)n;errno=ENOSYS;return -1;}
int _close(int f){(void)f;return -1;}
int _fstat(int f,struct stat *s){(void)f;s->st_mode=S_IFCHR;return 0;}
int _isatty(int f){(void)f;return 0;}
int _lseek(int f,int o,int w){(void)f;(void)o;(void)w;return -1;}
int _getpid(void){return 1;}
int _kill(int p,int s){(void)p;(void)s;errno=EINVAL;return -1;}
void _exit(int n){(void)n;for(;;){}}
