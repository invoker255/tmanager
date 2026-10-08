const v = (name) => `rgb(var(--${name}) / <alpha-value>)`

export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Hanken Grotesk"', 'system-ui', 'sans-serif']
      },
      colors: {
        canvas: v('canvas'),
        ink: v('ink'),
        accent: v('accent'),
        onaccent: v('on-accent'),
        danger: v('danger'),
        success: v('success')
      }
    }
  },
  plugins: []
}
