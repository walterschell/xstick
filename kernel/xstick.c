#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Walter");
MODULE_DESCRIPTION("Simple Module Skeleton");

static int __init xstick_init(void)
{
	return 0;
}
static void __exit xstick_cleanup(void)
{
}
module_init(xstick_init);
module_exit(xstick_cleanup);

