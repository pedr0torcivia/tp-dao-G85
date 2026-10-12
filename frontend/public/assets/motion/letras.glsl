precision mediump float;
/** @resolution */
uniform vec2 u_resolution;
/** @time */
uniform float u_time;
/** @label Intensidad @default 0.07 @range 0, 0.15 */
uniform float u_opacity;
/** @label Movimiento @default 1 @range 0, 1 */
uniform float u_motion;
/** @label Tinta @color @default #234D3C */
uniform vec3 u_ink;
/** @label Letra L */
uniform sampler2D u_L;
/** @label Letra e */
uniform sampler2D u_e;
/** @label Letra b */
uniform sampler2D u_b;
/** @label Letra r */
uniform sampler2D u_r;
/** @label Letra o */
uniform sampler2D u_o;
/** @label Letra s */
uniform sampler2D u_s;
vec2 localUV(vec2 p, vec2 center, float size, float phase) {
    float t = u_time * 0.36 + phase;
    vec2 drift = vec2(sin(t)*70.0/u_resolution.x, cos(t*0.77)*65.0/u_resolution.y) * u_motion;
    vec2 uv = (p - center - drift) * vec2(u_resolution.x/u_resolution.y,1.0) / size + 0.5;
    return uv;
}
float glyph(sampler2D tex, vec2 uv) {
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) return 0.0;
    return texture2D(tex, vec2(uv.x,1.0-uv.y)).a;
}
void main() {
    vec2 p = gl_FragCoord.xy / u_resolution;
    float a = 0.0;
    a=max(a,glyph(u_L,localUV(p,vec2(0.07194,0.85208),0.39583,0.00)));
    a=max(a,glyph(u_e,localUV(p,vec2(0.19167,0.89750),0.12500,0.81)));
    a=max(a,glyph(u_b,localUV(p,vec2(0.46028,0.93458),0.27083,1.62)));
    a=max(a,glyph(u_r,localUV(p,vec2(0.64125,0.88312),0.09375,2.43)));
    a=max(a,glyph(u_o,localUV(p,vec2(0.91458,0.86813),0.34375,3.24)));
    a=max(a,glyph(u_s,localUV(p,vec2(0.05472,0.63792),0.10417,4.05)));
    a=max(a,glyph(u_L,localUV(p,vec2(0.29986,0.66021),0.23958,4.86)));
    a=max(a,glyph(u_e,localUV(p,vec2(0.51556,0.63667),0.16667,5.67)));
    a=max(a,glyph(u_b,localUV(p,vec2(0.75819,0.66271),0.11458,6.48)));
    a=max(a,glyph(u_r,localUV(p,vec2(0.99375,0.52937),0.28125,7.29)));
    a=max(a,glyph(u_o,localUV(p,vec2(0.02681,0.27979),0.26042,8.10)));
    a=max(a,glyph(u_s,localUV(p,vec2(0.19035,0.35448),0.15104,8.91)));
    a=max(a,glyph(u_L,localUV(p,vec2(0.38472,0.42792),0.10417,9.72)));
    a=max(a,glyph(u_e,localUV(p,vec2(0.65153,0.27771),0.36458,10.53)));
    a=max(a,glyph(u_b,localUV(p,vec2(0.83729,0.29406),0.17188,11.34)));
    a=max(a,glyph(u_r,localUV(p,vec2(0.09208,0.06188),0.15625,12.15)));
    a=max(a,glyph(u_o,localUV(p,vec2(0.36764,-0.00146),0.32292,12.96)));
    a=max(a,glyph(u_s,localUV(p,vec2(0.50299,0.11052),0.09896,13.77)));
    a=max(a,glyph(u_L,localUV(p,vec2(0.73292,0.04063),0.21875,14.58)));
    a=max(a,glyph(u_e,localUV(p,vec2(0.91687,0.03969),0.14063,15.39)));
    a *= u_opacity;
    gl_FragColor = vec4(u_ink*a,a);
}
