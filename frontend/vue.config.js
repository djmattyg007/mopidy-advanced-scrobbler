module.exports = {
  lintOnSave: false,
  publicPath: "/advanced_scrobbler",
  chainWebpack: (config) => {
    const svgRule = config.module.rule("svg");

    svgRule.uses.clear();

    svgRule
      .use("vue-loader-v16")
      .loader("vue-loader-v16")
      .end()
      .use("vue-svg-loader")
      .loader("vue-svg-loader");
  },
};
