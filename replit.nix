
{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.cairo
    pkgs.pango
    pkgs.gdk-pixbuf
    pkgs.pkg-config
  ];
}
