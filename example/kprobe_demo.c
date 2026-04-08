#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kprobes.h>

static int handler_pre(struct kprobe *p, struct pt_regs *regs)
{
    // current 宏指向当前进程的 task_struct
    printk(KERN_INFO ">>> Kprobe triggered! Process '%s' (PID: %d) is calling %s, addr is %px\n", 
           current->comm, current->pid, p->symbol_name, p->addr);
    return 0;
}

#define MAX_KP_LEN 1000
// 改成这个 100% 能探测的函数
static struct kprobe kp_list[MAX_KP_LEN]; 
static char kp_sym_list[10][256] = {
    "do_filp_open",
    "path_openat",
    "d_alloc_parallel",
    "path_init",
    "link_path_walk",
};

static int __init kprobe_demo_init_single(struct kprobe *kp)
{
    int ret;

    ret = register_kprobe(kp);
    if (ret < 0) {
        pr_err("kprobe reg %s failed, ret = %d\n", kp->symbol_name, ret);
        return ret;
    }

    pr_info("✅ kprobe %s loaded successfully\n", kp->symbol_name);
    return 0;
}

static int __init kprobe_demo_init(void)
{
    for (int i = 0; i < MAX_KP_LEN; i++) {
        if (strlen(kp_sym_list[i]) == 0) {
            break;
        }
        struct kprobe *kp = &kp_list[i];
        kp->pre_handler = handler_pre;
        kp->symbol_name = kp_sym_list[i];
        kprobe_demo_init_single(kp);
    }
    return 0;
}

static void __exit kprobe_demo_exit(void)
{
    for (int i = 0; i < MAX_KP_LEN; i++) {
        if (strlen(kp_sym_list[i]) == 0) {
            break;
        }
        struct kprobe *kp = &kp_list[i];
        unregister_kprobe(kp);
    }
    pr_info("kprobe demo unloaded\n");
}

module_init(kprobe_demo_init);
module_exit(kprobe_demo_exit);
MODULE_LICENSE("GPL");