/* newlib calls these through __libc_init_array/__libc_fini_array.
 * The bare-metal image has no process-level constructor/destructor runtime. */
void _init(void)
{
}

void _fini(void)
{
}
