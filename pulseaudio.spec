%undefine _strict_symbol_defs_build

%global multilib_archs x86_64 %{ix86}
%global bash_completionsdir %(pkg-config --variable=completionsdir bash-completion 2>/dev/null || echo '/etc/bash_completion.d')

Name:           pulseaudio
Summary:        Improved Linux Sound Server
Version:        13.0
Release:        3
License:        LGPLv2+
URL:            https://www.freedesktop.org/wiki/Software/PulseAudio
Source0:        https://freedesktop.org/software/pulseaudio/releases/pulseaudio-%{version}.tar.xz
Source1:        https://freedesktop.org/software/pulseaudio/releases/pulseaudio-%{version}.tar.xz.sha256
Source5:        default.pa-for-gdm

Patch201:       pulseaudio-autostart.patch
Patch202:       pulseaudio-9.0-disable_flat_volumes.patch

BuildRequires:  automake libtool gcc-c++ bash-completion
BuildRequires:  m4 libtool-ltdl-devel intltool pkgconfig doxygen xmltoman libsndfile-devel
BuildRequires:  alsa-lib-devel glib2-devel gtk2-devel GConf2-devel avahi-devel check-devel
BuildRequires:  libatomic_ops-static libatomic_ops-devel bluez-libs-devel sbc-devel libXt-devel
BuildRequires:  xorg-x11-proto-devel libXtst-devel libXi-devel libSM-devel libX11-devel
BuildRequires:  libICE-devel xcb-util-devel openssl-devel orc-devel libtdb-devel speexdsp-devel
BuildRequires:  libasyncns-devel systemd-devel systemd dbus-devel libcap-devel fftw-devel
BuildRequires:  webrtc-audio-processing-devel

Obsoletes:      padevchooser < 1.0
Provides:       %{name}-module-x11 %{name}-module-bluetooth %{name}-libs %{name}-libs-glib2 %{name}-utils %{name}-esound-compat %{name}-module-zeroconf %{name}-module-gconf %{name}-module-gsettings
Obsoletes:      %{name}-module-x11 %{name}-module-bluetooth %{name}-libs %{name}-libs-glib2 %{name}-utils %{name}-esound-compat %{name}-module-zeroconf %{name}-module-gconf %{name}-module-gsettings

Requires(pre):  shadow-utils
Requires:       rtkit bluez >= 5.0

%description
PulseAudio is a sound server for Linux and other Unix like operating
systems. It is intended to be an improved drop-in replacement for the
Enlightened Sound Daemon (ESOUND).

%package        qpaeq
Summary:        Pulseaudio equalizer interface
Requires:       %{name} = %{version}-%{release}
Requires:       python2-qt5 dbus-python
%description    qpaeq
qpaeq is a equalizer interface for pulseaudio's equalizer sinks.

%package        devel
Summary:        Headers and libraries for PulseAudio client development
License:        LGPLv2+
Requires:       %{name} = %{version}-%{release}
Provides:       %{name}-libs-devel %{name}-libs-devel%{?_isa}
Obsoletes:      %{name}-libs-devel

%description    devel
Headers and libraries for developing applications that can communicate with
a PulseAudio sound server.

%package_help

%prep
%autosetup -n %{name}-%{version} -p1

sed -i.no_consolekit -e \
  's/^load-module module-console-kit/#load-module module-console-kit/' \
  src/daemon/default.pa.in

NOCONFIGURE=1 ./bootstrap.sh

%build
%configure \
  --disable-silent-rules --disable-rpath --with-system-user=pulse \
  --with-system-group=pulse --with-access-group=pulse-access \
  --disable-oss-output --disable-jack --disable-lirc \
  --disable-bluez4 --enable-bluez5 --enable-gconf \
  --enable-gsettings --enable-webrtc-aec --enable-tests

%make_build V=1

make doxygen

%install
%make_install

%ifarch %{multilib_archs}
pushd %{buildroot}%{_bindir}
%if "%{_libdir}" == "/usr/lib"
ln -s padsp padsp-32
%else
cp -a padsp padsp-32
sed -i -e "s|%{_libdir}/pulseaudio/libpulsedsp.so|/usr/lib/pulseaudio/libpulsedsp.so|g" padsp-32
%endif
popd
%endif

mkdir -p $RPM_BUILD_ROOT%{_prefix}/lib/udev/rules.d
mv -fv $RPM_BUILD_ROOT/lib/udev/rules.d/90-pulseaudio.rules $RPM_BUILD_ROOT%{_prefix}/lib/udev/rules.d

%delete_la

%check
%make_build check || TESTS_ERROR=$?
if [ "${TESTS_ERROR}" != "" ]; then
cat src/test-suite.log
exit $TESTS_ERROR
fi

%pre
getent group pulse-access >/dev/null || groupadd -r pulse-access
getent group pulse-rt >/dev/null || groupadd -r pulse-rt
getent group pulse >/dev/null || groupadd -f -g 171 -r pulse
if ! getent passwd pulse >/dev/null ; then
    if ! getent passwd 171 >/dev/null ; then
      useradd -r -u 171 -g pulse -d %{_localstatedir}/run/pulse -s /sbin/nologin -c "PulseAudio System Daemon" pulse
    else
      useradd -r -g pulse -d %{_localstatedir}/run/pulse -s /sbin/nologin -c "PulseAudio System Daemon" pulse
    fi
fi
exit 0

%posttrans
(grep '^load-module module-cork-music-on-phone$' %{_sysconfdir}/pulse/default.pa > /dev/null && \
 sed -i.rpmsave -e 's|^load-module module-cork-music-on-phone$|load-module module-role-cork|' \
 %{_sysconfdir}/pulse/default.pa
) ||:

%ldconfig_scriptlets

%files
%defattr(-,root,root)
%license LICENSE GPL LGPL
%config(noreplace) %{_sysconfdir}/pulse/daemon.conf
%config(noreplace) %{_sysconfdir}/pulse/*.pa
%config(noreplace) %{_sysconfdir}/pulse/client.conf
%{_sysconfdir}/dbus-1/system.d/pulseaudio-system.conf
%{_sysconfdir}/xdg/autostart/pulseaudio.desktop
%{bash_completionsdir}/*
%{_userunitdir}/pulseaudio.*
%{_bindir}/esdcompat
%{_bindir}/pulseaudio
%{_bindir}/start-pulseaudio-x11
%{_bindir}/pacat
%{_bindir}/pacmd
%{_bindir}/pactl
%{_bindir}/paplay
%{_bindir}/parec
%{_bindir}/pamon
%{_bindir}/parecord
%{_bindir}/pax11publish
%{_bindir}/padsp
%{_bindir}/pasuspender
%{_bindir}/pa-info
%ifarch %{multilib_archs}
%{_bindir}/padsp-32
%endif
%{_libdir}/*.so.*
%{_libdir}/pulseaudio/*.so
%{_libdir}/pulse-%{version}/modules/*.so
%exclude %{_libdir}/pulse-%{version}/modules/module-equalizer-sink.so
%exclude %{_libdir}/pulse-%{version}/modules/module-detect.so

%{_prefix}/lib/udev/rules.d/90-pulseaudio.rules
%{_libexecdir}/pulse/*-helper
%{_datadir}/locale/*
%{_datadir}/pulseaudio/alsa-mixer/*/
%{_datadir}/zsh/site-functions/_pulseaudio
%{_datadir}/GConf/gsettings/pulseaudio.convert

%files qpaeq
%defattr(-,root,root)
%{_bindir}/qpaeq
%{_libdir}/pulse-%{version}/modules/module-equalizer-sink.so

%files devel
%defattr(-,root,root)
%{_includedir}/pulse/
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc
%{_datadir}/vala/vapi/*
%{_libdir}/cmake/PulseAudio/

%files help
%defattr(-,root,root)
%doc README doxygen/html
%{_mandir}/man*/*
%{_datadir}/glib-2.0/schemas/org.freedesktop.pulseaudio.gschema.xml

%changelog
* Sun Sep 14 2020 xinghe <xinghe1@huawei.com> - 13.0-3
- remove repeat gdm-hooks packages

* Fri Aug 21 2020 lunankun <lunankun@huawei.com> - 13.0-2
- Type:bugfix
- Id:NA
- SUG:NA
- DESC:release +1 for rebuild

* Fri Apr 24 2020 Chunsheng Luo <luochunsheng@huawei.com> - 13.0-1
- update to version 13.0

* Fri Oct 18 2019 shenyangyang <shenyangyang4@huawei.com> - 12.2-3
- Type:enhancement
- ID:NA
- SUG:NA
- DESC:add provides of pulseaudio-libs-devel(aarch-64) needed by libmikmod-devel

* Mon Sep 16 2019 openEuler Buildteam <buildteam@openeuler.org> - 12.2-2
- Package init
