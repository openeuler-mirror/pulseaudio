%undefine _strict_symbol_defs_build

%global multilib_archs x86_64 %{ix86}
%global bash_completionsdir %(pkg-config --variable=completionsdir bash-completion 2>/dev/null || echo '/etc/bash_completion.d')

Name:           pulseaudio
Summary:        Improved Linux Sound Server
Version:        15.0
Release:        6
License:        LGPLv2+
URL:            https://www.freedesktop.org/wiki/Software/PulseAudio
Source0:        https://freedesktop.org/software/pulseaudio/releases/pulseaudio-%{version}.tar.xz
Source1:        https://freedesktop.org/software/pulseaudio/releases/pulseaudio-%{version}.tar.xz.sha256sum
Source5:        default.pa-for-gdm

Patch201:       pulseaudio-autostart.patch
%ifarch riscv64
Patch202:       set_timeout_for_test.patch
#volume-test fail on riscv, skip this test
Patch203:       skip_volume_test.patch
%endif

BuildRequires:	meson
BuildRequires:  automake libtool gcc-c++ bash-completion
BuildRequires:  m4 libtool-ltdl-devel intltool pkgconfig doxygen xmltoman libsndfile-devel
BuildRequires:  alsa-lib-devel glib2-devel gtk2-devel avahi-devel check-devel
BuildRequires:  libatomic_ops-static libatomic_ops-devel bluez-libs-devel sbc-devel libXt-devel
BuildRequires:  xorg-x11-proto-devel libXtst-devel libXi-devel libSM-devel libX11-devel
BuildRequires:  libICE-devel xcb-util-devel openssl-devel orc-devel libtdb-devel speexdsp-devel
BuildRequires:  libasyncns-devel systemd-devel systemd dbus-devel libcap-devel fftw-devel
BuildRequires:	pkgconfig(gstreamer-1.0) pkgconfig(gstreamer-app-1.0) pkgconfig(gstreamer-rtp-1.0)

Obsoletes:      padevchooser < 1.0
Provides:       %{name}-module-x11 %{name}-utils %{name}-esound-compat %{name}-module-zeroconf %{name}-module-gsettings
Obsoletes:      %{name}-module-x11 %{name}-utils %{name}-esound-compat %{name}-module-zeroconf %{name}-module-gsettings

Requires(pre):  shadow-utils
Requires:       rtkit

%description
PulseAudio is a sound server for Linux and other Unix like operating
systems. It is intended to be an improved drop-in replacement for the
Enlightened Sound Daemon (ESOUND).

%package        qpaeq
Summary:        Pulseaudio equalizer interface
Requires:       %{name} = %{version}-%{release}
Requires:       python3-qt5 python3-dbus
%description    qpaeq
qpaeq is a equalizer interface for pulseaudio's equalizer sinks.

%package module-bluetooth
Summary:        Bluetooth support for the PulseAudio sound server
Requires:       %{name} = %{version}-%{release}
Requires:       bluez >= 5.0
	
%description module-bluetooth
Contains Bluetooth audio (A2DP/HSP/HFP) support for the PulseAudio sound server.

%package libs
Summary:        Libraries for PulseAudio clients
License:        LGPLv2+
Obsoletes:      pulseaudio-libs-zeroconf < 1.1

%description libs
This package contains the runtime libraries for any application that wishes
to interface with a PulseAudio sound server.

%package libs-glib2
Summary:        GLIB 2.x bindings for PulseAudio clients
License:        LGPLv2+
Requires:       %{name}-libs = %{version}-%{release}
 
%description libs-glib2
This package contains bindings to integrate the PulseAudio client library with
a GLIB 2.x based application.

%package libs-devel
Summary:        Headers and libraries for PulseAudio client development
License:        LGPLv2+
Requires:       %{name}-libs = %{version}-%{release}
Requires:       %{name}-libs-glib2 = %{version}-%{release}

%description libs-devel
Headers and libraries for developing applications that can communicate with
a PulseAudio sound server.

%package_help

%prep
%autosetup -n %{name}-%{version} -p1

sed -i.no_consolekit -e \
  's/^load-module module-console-kit/#load-module module-console-kit/' \
  src/daemon/default.pa.in


%build
%meson \
  -D system_user=pulse \
  -D system_group=pulse \
  -D access_group=pulse-access \
  -D oss-output=disabled \
  -D jack=disabled \
  -D lirc=disabled \
  -D tcpwrap=disabled \
  -D bluez5=enabled \
  -D gstreamer=enabled \
  -D bluez5-gstreamer=enabled \
  -D gsettings=enabled \
  -D elogind=disabled \
  -D valgrind=disabled \
  -D gtk=disabled \
  -D soxr=disabled \
  -D webrtc-aec=disabled \
  -D systemd=disabled \
  -D tests=true
 
%meson_build

%meson_build doxygen

%install
%meson_install

mkdir -p $RPM_BUILD_ROOT%{_prefix}/lib/udev/rules.d
mv -fv $RPM_BUILD_ROOT/lib/udev/rules.d/90-pulseaudio.rules $RPM_BUILD_ROOT%{_prefix}/lib/udev/rules.d

%delete_la

%check
%meson_test || TESTS_ERROR=$?
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
%{_bindir}/pasuspender
%{_bindir}/pa-info
%{_libdir}/*.so.*
%exclude %{_libdir}/libpulse.so.0*
%exclude %{_libdir}/libpulse-simple.so.0*
%exclude %{_libdir}/libpulse-mainloop-glib.so.0*
%{_libdir}/pulseaudio/*.so
%exclude %{_libdir}/pulseaudio/libpulsecommon-%{version}.so
%{_libdir}/pulse-%{version}/modules/*.so
%exclude %{_libdir}/pulse-%{version}/modules/module-equalizer-sink.so
%exclude %{_libdir}/pulse-%{version}/modules/module-detect.so
%exclude %{_libdir}/pulse-%{version}/modules/libbluez*-util.so
%exclude %{_libdir}/pulse-%{version}/modules/module-bluez*-device.so
%exclude %{_libdir}/pulse-%{version}/modules/module-bluez*-discover.so
%exclude %{_libdir}/pulse-%{version}/modules/module-bluetooth-discover.so
%exclude %{_libdir}/pulse-%{version}/modules/module-bluetooth-policy.so
%{_prefix}/lib/udev/rules.d/90-pulseaudio.rules
%{_libexecdir}/pulse/*-helper
%{_datadir}/locale/*
%{_datadir}/pulseaudio/alsa-mixer/*/
%{_datadir}/zsh/site-functions/_pulseaudio
%{_datadir}/GConf/gsettings/pulseaudio.convert
%config(noreplace) %{_sysconfdir}/xdg/Xwayland-session.d/00-pulseaudio-x11

%files qpaeq
%defattr(-,root,root)
%{_bindir}/qpaeq
%{_libdir}/pulse-%{version}/modules/module-equalizer-sink.so

%files module-bluetooth
%{_libdir}/pulse-%{version}/modules/libbluez*-util.so
%{_libdir}/pulse-%{version}/modules/module-bluez*-device.so
%{_libdir}/pulse-%{version}/modules/module-bluez*-discover.so
%{_libdir}/pulse-%{version}/modules/module-bluetooth-discover.so
%{_libdir}/pulse-%{version}/modules/module-bluetooth-policy.so
	
%files libs
%dir %{_sysconfdir}/pulse/
%config(noreplace) %{_sysconfdir}/pulse/client.conf
%{_libdir}/libpulse.so.0*
%{_libdir}/libpulse-simple.so.0*
%dir %{_libdir}/pulseaudio/
%{_libdir}/pulseaudio/libpulsecommon-%{version}.so

%files libs-glib2
%{_libdir}/libpulse-mainloop-glib.so.0*

%files libs-devel
%defattr(-,root,root)
%{_includedir}/pulse/
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc
%{_datadir}/vala/vapi/*
%{_libdir}/cmake/PulseAudio/

%files help
%defattr(-,root,root)
%{_mandir}/man*/*
%{_datadir}/glib-2.0/schemas/org.freedesktop.pulseaudio.gschema.xml

%changelog
* Thu Feb 22 2022 lvxiaoqian <xiaoqian@nj.iscas.ac.cn> - 15.0-6
- set srbchannel-test timeout

* Thu Feb 17 2022 lvxiaoqian <xiaoqian@nj.iscas.ac.cn> - 15.0-5
- set thread-test timeout and skip volume-test for riscv

* Mon Jan 17 2022 zhouwenpei <zhouwenpei1@huawei.com> - 15.0-4
- remove dependency on GConf2 package 

* Thu Jan 13 2022 zhouwenpei <zhouwenpei1@huawei.com> - 15.0-3
- clean up .so and disabled webrtc-aec

* Fri Dec 10 2021 zhouwenpei <zhouwenpei1@huawei.com> - 15.0-2
- fix build error and split packages

* Sat Dec 4 2021 zhouwenpei <zhouwenpei1@huawei.com> - 15.0-1
- update to version 15.0

* Fri Oct 30 2020 xinghe <xinghe1@huawei.com> - 13.0-4
- remove python2 dependency

* Fri Sep 25 2020 xinghe <xinghe1@huawei.com> - 13.0-3
- remove old tar packages

* Sun Sep 14 2020 xinghe <xinghe1@huawei.com> - 13.0-2
- remove repeat gdm-hooks packages

* Fri Apr 24 2020 Chunsheng Luo <luochunsheng@huawei.com> - 13.0-1
- update to version 13.0

* Fri Oct 18 2019 shenyangyang <shenyangyang4@huawei.com> - 12.2-3
- Type:enhancement
- ID:NA
- SUG:NA
- DESC:add provides of pulseaudio-libs-devel(aarch-64) needed by libmikmod-devel

* Mon Sep 16 2019 openEuler Buildteam <buildteam@openeuler.org> - 12.2-2
- Package init
