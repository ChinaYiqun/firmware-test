#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/mod_devicetable.h>
#include <linux/regmap.h>
#include <linux/io.h>
#include <linux/slab.h>
#include <linux/err.h>

#define DRIVER_NAME "vendor-example-regmap"
#define REG_CTRL   0x00
#define REG_STATUS 0x04
#define REG_MAX    0xFF

struct example_regmap {
	struct regmap *regmap;
};

static const struct regmap_config example_regmap_config = {
	.reg_bits    = 32,
	.val_bits    = 32,
	.reg_stride  = 4,
	.max_register = REG_MAX,
};

static int example_regmap_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct example_regmap *r;
	void __iomem *base;
	unsigned int status;
	int ret;

	r = devm_kzalloc(dev, sizeof(*r), GFP_KERNEL);
	if (!r)
		return -ENOMEM;

	base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(base))
		return PTR_ERR(base);

	r->regmap = devm_regmap_init_mmio(dev, base, &example_regmap_config);
	if (IS_ERR(r->regmap))
		return PTR_ERR(r->regmap);

	ret = regmap_write(r->regmap, REG_CTRL, 0x1);
	if (ret)
		return ret;

	ret = regmap_read(r->regmap, REG_STATUS, &status);
	if (ret)
		return ret;

	platform_set_drvdata(pdev, r);
	dev_info(dev, "%s: probed, status=0x%08x\n", DRIVER_NAME, status);
	return 0;
}

static int example_regmap_remove(struct platform_device *pdev)
{
	(void)pdev;
	return 0;
}

static const struct of_device_id example_regmap_of_match[] = {
	{ .compatible = "vendor,example-regmap" },
	{},
};
MODULE_DEVICE_TABLE(of, example_regmap_of_match);

static struct platform_driver example_regmap_driver = {
	.probe  = example_regmap_probe,
	.remove = example_regmap_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = example_regmap_of_match,
	},
};
module_platform_driver(example_regmap_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("EmbedEval");
MODULE_DESCRIPTION("Platform driver using regmap_mmio abstraction");
