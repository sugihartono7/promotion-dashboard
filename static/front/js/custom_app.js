function showhide(a, b) {
    "1" != a ? (obj1 = document.getElementById(b), obj1.style.display = "") : (obj1 = document.getElementById(b), obj1.style.display = "none")
}

function hide(a) {
    obj1 = document.getElementById(a), obj1.style.display = "none"
}

function chekouts() {
    $("input#tocheckout").val("y")
}

function couts() {
    $("input#tocheckout").val(""), $("button#topayment").attr("onclick", "").unbind("click")
}

function qtyupdates() {
    clearTimeout(to), to = setTimeout(function() {
        $("#update").submit()
    }, 1e3)
}
jQuery.noConflict(), $(function() {
    $(document).ready(function() {
        $(".star").rating(), $(".star").click(function() {
            $("input#rating").val($(this).text())
        }), $("div.rating-cancel a").click(function() {
            $("input#rating").val("").css("display", "block")
        }), $.browser.msie && $.browser.version.substr(0, 1) < 8 && $(".top_ls").before('<div style="width:100%;background:red"><p style="width:960px;margin:auto;text-align:center;font-size:13px;padding:10px 0;"><a style="color:#fff;" href="http://windows.microsoft.com/en-IN/internet-explorer/products/ie/home">Hey Sparky Update your Browser its too old click here to update</a></p></div>'), $(".smartcart").smartcart(), $(".bubcrt").smartcartCountItems(), $("#smart-form").unbind().bind("submit", function() {
            var a = $(this),
                b = $(a).serialize(),
                d = ($("#pd_opsi option:selected").text(), $("#tocheckout").val());
            return $(".alert").removeClass("alert-success"), $(".alert").removeClass("alert-error"), $(".alert").html('<img src="' + template_url + '/images/ajax-loader.gif" /> Please wait'), $(".alert").fadeIn(), $.ajax({
                type: "POST",
                url: template_crt,
                data: b + "&command=update&topayment=" + d,
                success: function(a) {
                    if ("onpros" == a) {
                        var b = cart_url.replace("shop/cart", "shop/checkout" + template_chk);
                        return window.location.href = b, !1
                    }
                    "error" == a ? ($(".alert").text(""), $(".alert").hide(), $(".alert").addClass("alert-error"), $(".alert").text("Error occurred. Please try  again"), $(".alert").show(), $(".alert").delay(1e4).fadeOut()) : $(".smart_cart").load(cart_url + " .smart_cart", function() {
                        $(".alert").hide(), $.getScript(template_url + "/js/custom_app.js"), $("#continue-shopping-btn").click(function() {})
                    })
                }
            }), !1
        }), $("#prov").change(function() {
            var a = $(this).val(),
                b = "type=prov&req=" + a;
            $(".redwarnkurir").hide(), $("#loadingmessage").show(), $("#dom_kota").prop("disabled", !0), $("#pm_kecamatan").prop("disabled", !0), $("#dom_kota").val(""), $("#pm_kecamatan").val(""), $("#ongkir-table").empty(), $.ajax({
                type: "POST",
                url: template_url + "/lib/cart/ajax/lib.rest.php",
                data: b,
                cache: !1,
                success: function(a) {
                    $("#dom_kota").prop("disabled", !1), $("#loadingmessage").hide(), $("#dom_kota").html(a)
                }
            })
        }), $("#dom_kota").change(function() {
            var a = $(this).val(),
                b = "type=city&req=" + a;
            $(".redwarnkurir").hide(), $("#loadingmessage2").show(), $("#pm_kecamatan").prop("disabled", !0), $("#ongkir-table").empty(), $.ajax({
                type: "POST",
                url: template_url + "/lib/cart/ajax/lib.rest.php",
                data: b,
                cache: !1,
                success: function(a) {
                    $("#pm_kecamatan").prop("disabled", !1), $("#dom_kurir").prop("disabled", !1), $("#kecatan2").prop("disabled", !1), $("#loadingmessage2").hide(), $("#pm_kecamatan").html(a), $("#kecatan2").html(a)
                }
            })
        }), $("#pm_kecamatan").change(function() {
            var a = $(this).val(),
                b = 'cek',
                u = $('#prov').val(),
                c = "type=getprice&city=" + b + "&req=" + a + "&prov=" + u;
            $(".redwarnkurir").hide(), $("#loadingmessage2").show(), $(".ongk").show(), $("#ongkir").empty(), $("#total").html("Rp " + $.number(ordertotal, 0, ",", ".") + ",-"), $("#total2").html("Rp " + $.number(ordertotal, 0, ",", ".") + ",-"), $("input#totalorder").val(ordertotal), $.ajax({
                type: "POST",
                url: template_url + "/lib/cart/ajax/lib.rest.php",
                data: c,
                cache: !1,
                success: function(a) {
                    $("#loadingmessage2").hide(), $(".ongk").hide(), $("#ongkir").html(a);
                    "Gratis Ongkir" == a && ($("input#ongkirt").val("0"), $("input#ongkirpkg").val(a));
                }
            })
        }), $("#cekresi").click(function() {
            var a = $("input[name=awb]").val(),
                b = $("select[name=kurir]").val();
            if ("#" == a || "" == a) return $(".redwarnkurir").html("Anda Belum Mengisi No Resi"), $(".redwarnkurir").slideDown(), !1;
            if ($(".redwarnkurir").hide(), "#" == b || "" == b) return $(".redwarnkurir").html("Anda Belum Memilih Kurir"), $(".redwarnkurir").slideDown(), !1;
            $(".redwarnkurir").hide();
            //alert(a);
            var c = "type=awb&awb=" + a + "&kurir=" + b;
            $(".resii").show(), $("#resis").empty(), $.ajax({
                type: "POST",
                url: template_url + "/lib/cart/ajax/lib.smarttoko.php",
                data: c,
                cache: !1,
                success: function(a) {
                    $(".resii").hide(), $("#resis").html(a)
                }
            })
        }), $("#smtx_wishlist").click(function() {
            var a = $("input[name=productid]").val();
            var c = "command=wishlist&productid=" + a;
            alert(a);
            $.ajax({
                type: "POST",
                url: template_crt,
                data: c,
                cache: !1,
                success: function(a) {
                    $("#pwishli").html('<button class="btn btn-warning btn-xs btn-dewishlist"><i class="glyphicon glyphicon-remove"></i> Sudah didalam wishlist</button>')
                }
            })
        }), $("#cekongkir").click(function() {
            var a = $("select[name=kecatan2]").val(),
                b = $("select[name=kurir]").val();
            if ("#" == a || "" == a) return $(".redwarnkurir").html("Anda Belum Memilih Tujuan Pengiriman"), $(".redwarnkurir").slideDown(), !1;
            if ($(".redwarnkurir").hide(), "#" == b || "" == b) return $(".redwarnkurir").html("Anda Belum Memilih Kurir"), $(".redwarnkurir").slideDown(), !1;
            $(".redwarnkurir").hide();
            var c = "type=getprice&pagez=getdata&city=" + b + "&req=" + a;
            $(".ongk").show(), $("#ongkir").empty(), $.ajax({
                type: "POST",
                url: template_url + "/lib/cart/ajax/lib.rest.php",
                data: c,
                cache: !1,
                success: function(a) {
                    $(".ongk").hide(), $("#ongkir").html(a)
                }
            })
        }), $("input.shipping").on("change", function() {
            var t = $(this).val(),
                e = $("input[name=inputadres]:checked").val(),
                a = "type=getprice&cek=" + e + "&pagez=getdataup&req=" + t;
            $("#loadingmessage2").show(), $(".ongk").show(), $("#ongkir").empty(), $.ajax({
                type: "POST",
                url: template_url + "/lib/cart/ajax/lib.rest.php",
                data: a,
                cache: !1,
                success: function(t) {
                    $("#loadingmessage2").hide(), $(".ongk").hide(), $("#checkout-address :input").attr("disabled", "disabled"), $("#ongkir").html(t)
                }
            })
        }), $("#ongkir").change(function() {
            var a = $("#cost option:selected").val(),
                b = a.split(","),
                c = parseFloat(b[1], 10) || 0,
                d = ordertotal + c;
            $("#total").html("Rp " + $.number(d, 0, ",", ".") + ",-"), $("#total2").html("Rp " + $.number(d, 0, ",", ".") + ",-"), $("input#ongkirt").val(c), $("input#ongkirpkg").val(b[0]), $("input#totalorder").val(d)
        }), $("#smart-form .smrt-clear-btn").click(function() {
            var a = $("#smart-form"),
                b = $(this).attr("data-item"),
                a = $("#smart-form");
            a.submit(), $.ajax({
                type: "POST",
                url: template_crt,
                data: "&command=delete&pid=" + b,
                success: function(a) {
                    $.getScript(template_url + "/js/custom_app.js")
                }
            })
        }), $("#smart-form .smrt-kpn-btn").click(function() {
            var a = $("#smart-form"),
                a = $("#smart-form");
            a.submit(), $.ajax({
                type: "POST",
                url: template_crt,
                data: "&command=removekpn",
                success: function(a) {
                    $.getScript(template_url + "/js/custom_app.js")
                }
            })
        }), $(".cart-empty-button").click(function() {
            $(".alert").removeClass("alert-success"), $(".alert").removeClass("alert-error"), $(".alert").html('<img src="' + template_url + '/images/ajax-loader.gif" /> Please wait'), $(".alert").fadeIn(), $.ajax({
                type: "POST",
                url: template_crt,
                data: "&command=clear",
                success: function(a) {
                    "error" == a ? ($(".alert").text(""), $(".alert").hide(), $(".alert").addClass("alert-error"), $(".alert").text("Error occurred. Please try  again"), $(".alert").show(), $(".alert").delay(1e4).fadeOut()) : $(".smart_cart").load(cart_url + " .smart_cart", function() {
                        $(".alert").hide(), $(".smart_cart").removeClass("smrt-loading"), $.getScript(template_url + "/js/custom_app.js")
                    })
                }
            })
        })
    }), $.fn.smartcart = function() {
        $(".smartcart-form").unbind().bind("submit", function() {
            var a = $(this),
                b = $(a).serialize();
            $("#pd_opsi option:selected").text();
            return $.fancybox.showLoading(), $.ajax({
                type: "POST",
                url: template_crt,
                data: b,
                success: function(a) {
                    $.getScript(template_url + "/js/custom_app.js"), $.fancybox(a, {
                        modal: !0
                    })
                }
            }), !1
        })
    }, $.fn.smartcartCountItems = function() {
        return this.each(function() {
            $(this).html();
            $(this).addClass("cart-count");
            var b = $(this);
            $(this).html("-"), $.ajax({
                type: "POST",
                url: template_crt,
                data: "command=count",
                success: function(a) {
                    b.html(a)
                }
            })
        }), !1
    }
}), $(document).ready(function() {
    var a = $(".info-toko"),
        b = $(".cart-fade");
    $(window).scroll(function() {
        $(window).width() > 685 && ($(this).scrollTop() > 230 ? (a.addClass("f-nav"), b.removeClass("cshow")) : (a.removeClass("f-nav"), b.addClass("cshow")))
    })
}), $(document).ready(function() {
    $("#menu-wrap").prepend('<div id="menu-trigger">Menu</div>'), $("#menu-trigger").on("click", function() {
        $(".menu").slideToggle(), $(".menu").parent().siblings().children().next().slideUp()
    });
    var a = null != navigator.userAgent.match(/iPad/i);
    a && $("#menu ul").addClass("no-transition")
}), $(document).ready(function() {
    $("#product_zoom").elevateZoom({
        zoomWindowPosition: "detailsingle_boxleft",
        gallery: "gallery_01",
        responsive: !0,
        zoomWindowWidth: "266",
        zoomWindowHeight: "280",
        borderColour: "#ccc",
        borderSize: "1",
        cursor: "pointer",
        galleryActiveClass: "active",
        imageCrossfade: !0,
        loadingIcon: template_url + "/css/spinner.gif"
    }), $("#product_zoom").bind("click", function(a) {
        var b = $("#product_zoom").data("elevateZoom");
        return $.fancybox(b.getGalleryList()), !1
    })
}), $(document).ready(function() {
    $("#tab1").fadeIn("slow"), $("ul#nav li a").click(function() {
        $("ul#nav li a").removeClass("active"), $(this).addClass("active"), $(".tab_konten").hide();
        var a = $(this).attr("href");
        return $(a).fadeIn("slow"), !1
    })
}), $(document).ready(function() {
    if ($("#inline").length > 0) {
        if ("yes" == $.cookie("visited")) return !1;
        setTimeout(function() {
            $.fancybox.open({
                href: "#inline"
            })
        }, 15e3), $.cookie("visited", "yes", {
            expires: 1
        })
    }
    $("#daftary").change(function() {
        this.checked ? $("#toggle").fadeIn("slow") : $("#toggle").fadeOut("slow")
    }), $(".inputadres").change(function() {
        alert();
        this.checked ? ($("#checkout-address").fadeIn("slow"), $("#ongkir").html("Pilih Alamat"), $("input[name=shippingaddress]").prop("checked", !1), $("#checkout-address :input").removeAttr("disabled"), $("input[name=shippingaddress]").attr("disabled", "disabled")) : ($("#checkout-address").fadeOut("slow"), $("input[name=shippingaddress]").prop("checked", !1), $("#checkout-address :input").attr("disabled", "disabled"), $("input[name=shippingaddress]").removeAttr("disabled"))
    })
});
var to;
var stop_notification_till = 1;
! function() {
    function t() {
        if (oncheckout == 0)
            for (var t = [template_url + "/js/quickme.min.js"], e = 0; e < t.length; e++) {
                var n = document.createElement("script");
                n.type = "text/javascript", n.async = !0, n.src = t[e];
                var a = document.getElementsByTagName("script")[0];
                a.parentNode.insertBefore(n, a)
            }
    }
    window.attachEvent ? window.attachEvent("onload", t) : window.addEventListener("load", t, !1)
}();
$(document).on("click", ".panel-heading span.icon_minim", function(e) {
    var n = $(this);
    n.hasClass("panel-collapsed") ? (n.parents(".panel").find(".panel-body").slideDown(), n.removeClass("panel-collapsed"), n.removeClass("icon-chevron-up glyphicon-chevron-up").addClass("icon-chevron-down glyphicon-chevron-down"), $(window).width() < 425 && ($(".insidewatj").addClass("insidewatj-lite"), $(".watjtitle").addClass("watjtitle-lite"))) : (n.parents(".panel").find(".panel-body").slideUp(), n.addClass("panel-collapsed"), n.removeClass("icon-chevron-down glyphicon-chevron-down").addClass("icon-chevron-up glyphicon-chevron-up"), $(window).width() < 425 && ($(".msg_container_base").hide(), $(".insidewatj").removeClass("insidewatj-lite"), $(".watjtitle").removeClass("watjtitle-lite")))
}), $(document).on("click", ".icon_close", function(e) {
    $(".watjbanner").remove()
});
/** Easing **/
jQuery.extend(jQuery.easing, {
    easeInQuad: function(a, b, c, d, e) {
        return d * (b /= e) * b + c
    },
    easeOutQuad: function(a, b, c, d, e) {
        return -d * (b /= e) * (b - 2) + c
    },
    easeInOutQuad: function(a, b, c, d, e) {
        return (b /= e / 2) < 1 ? d / 2 * b * b + c : -d / 2 * (--b * (b - 2) - 1) + c
    },
    easeInCubic: function(a, b, c, d, e) {
        return d * (b /= e) * b * b + c
    },
    easeOutCubic: function(a, b, c, d, e) {
        return d * ((b = b / e - 1) * b * b + 1) + c
    },
    easeInOutCubic: function(a, b, c, d, e) {
        return (b /= e / 2) < 1 ? d / 2 * b * b * b + c : d / 2 * ((b -= 2) * b * b + 2) + c
    },
    easeInQuart: function(a, b, c, d, e) {
        return d * (b /= e) * b * b * b + c
    },
    easeOutQuart: function(a, b, c, d, e) {
        return -d * ((b = b / e - 1) * b * b * b - 1) + c
    },
    easeInOutQuart: function(a, b, c, d, e) {
        return (b /= e / 2) < 1 ? d / 2 * b * b * b * b + c : -d / 2 * ((b -= 2) * b * b * b - 2) + c
    },
    easeInQuint: function(a, b, c, d, e) {
        return d * (b /= e) * b * b * b * b + c
    },
    easeOutQuint: function(a, b, c, d, e) {
        return d * ((b = b / e - 1) * b * b * b * b + 1) + c
    },
    easeInOutQuint: function(a, b, c, d, e) {
        return (b /= e / 2) < 1 ? d / 2 * b * b * b * b * b + c : d / 2 * ((b -= 2) * b * b * b * b + 2) + c
    },
    easeInSine: function(a, b, c, d, e) {
        return -d * Math.cos(b / e * (Math.PI / 2)) + d + c
    },
    easeOutSine: function(a, b, c, d, e) {
        return d * Math.sin(b / e * (Math.PI / 2)) + c
    },
    easeInOutSine: function(a, b, c, d, e) {
        return -d / 2 * (Math.cos(Math.PI * b / e) - 1) + c
    },
    easeInExpo: function(a, b, c, d, e) {
        return 0 == b ? c : d * Math.pow(2, 10 * (b / e - 1)) + c
    },
    easeOutExpo: function(a, b, c, d, e) {
        return b == e ? c + d : d * (-Math.pow(2, -10 * b / e) + 1) + c
    },
    easeInOutExpo: function(a, b, c, d, e) {
        return 0 == b ? c : b == e ? c + d : (b /= e / 2) < 1 ? d / 2 * Math.pow(2, 10 * (b - 1)) + c : d / 2 * (-Math.pow(2, -10 * --b) + 2) + c
    },
    easeInCirc: function(a, b, c, d, e) {
        return -d * (Math.sqrt(1 - (b /= e) * b) - 1) + c
    },
    easeOutCirc: function(a, b, c, d, e) {
        return d * Math.sqrt(1 - (b = b / e - 1) * b) + c
    },
    easeInOutCirc: function(a, b, c, d, e) {
        return (b /= e / 2) < 1 ? -d / 2 * (Math.sqrt(1 - b * b) - 1) + c : d / 2 * (Math.sqrt(1 - (b -= 2) * b) + 1) + c
    },
    easeInElastic: function(a, b, c, d, e) {
        var f = 1.70158,
            g = 0,
            h = d;
        if (0 == b) return c;
        if (1 == (b /= e)) return c + d;
        if (g || (g = .3 * e), h < Math.abs(d)) {
            h = d;
            var f = g / 4
        } else var f = g / (2 * Math.PI) * Math.asin(d / h);
        return -(h * Math.pow(2, 10 * (b -= 1)) * Math.sin((b * e - f) * (2 * Math.PI) / g)) + c
    },
    easeOutElastic: function(a, b, c, d, e) {
        var f = 1.70158,
            g = 0,
            h = d;
        if (0 == b) return c;
        if (1 == (b /= e)) return c + d;
        if (g || (g = .3 * e), h < Math.abs(d)) {
            h = d;
            var f = g / 4
        } else var f = g / (2 * Math.PI) * Math.asin(d / h);
        return h * Math.pow(2, -10 * b) * Math.sin((b * e - f) * (2 * Math.PI) / g) + d + c
    },
    easeInOutElastic: function(a, b, c, d, e) {
        var f = 1.70158,
            g = 0,
            h = d;
        if (0 == b) return c;
        if (2 == (b /= e / 2)) return c + d;
        if (g || (g = e * (.3 * 1.5)), h < Math.abs(d)) {
            h = d;
            var f = g / 4
        } else var f = g / (2 * Math.PI) * Math.asin(d / h);
        return b < 1 ? -.5 * (h * Math.pow(2, 10 * (b -= 1)) * Math.sin((b * e - f) * (2 * Math.PI) / g)) + c : h * Math.pow(2, -10 * (b -= 1)) * Math.sin((b * e - f) * (2 * Math.PI) / g) * .5 + d + c
    },
    easeInBack: function(a, b, c, d, e, f) {
        return void 0 == f && (f = 1.70158), d * (b /= e) * b * ((f + 1) * b - f) + c
    },
    easeOutBack: function(a, b, c, d, e, f) {
        return void 0 == f && (f = 1.70158), d * ((b = b / e - 1) * b * ((f + 1) * b + f) + 1) + c
    },
    easeInOutBack: function(a, b, c, d, e, f) {
        return void 0 == f && (f = 1.70158), (b /= e / 2) < 1 ? d / 2 * (b * b * (((f *= 1.525) + 1) * b - f)) + c : d / 2 * ((b -= 2) * b * (((f *= 1.525) + 1) * b + f) + 2) + c
    },
    easeInBounce: function(a, b, c, d, e) {
        return d - jQuery.easing.easeOutBounce(a, e - b, 0, d, e) + c
    },
    easeOutBounce: function(a, b, c, d, e) {
        return (b /= e) < 1 / 2.75 ? d * (7.5625 * b * b) + c : b < 2 / 2.75 ? d * (7.5625 * (b -= 1.5 / 2.75) * b + .75) + c : b < 2.5 / 2.75 ? d * (7.5625 * (b -= 2.25 / 2.75) * b + .9375) + c : d * (7.5625 * (b -= 2.625 / 2.75) * b + .984375) + c
    },
    easeInOutBounce: function(a, b, c, d, e) {
        return b < e / 2 ? .5 * jQuery.easing.easeInBounce(a, 2 * b, 0, d, e) + c : .5 * jQuery.easing.easeOutBounce(a, 2 * b - e, 0, d, e) + .5 * d + c
    }
});
/*! jQuery number 2.1.0 (c) 
github.com/teamdf/jquery-number | opensource.teamdf.com/license */
(function(h) {
    function r(d, a) {
        if (this.createTextRange) {
            var c = this.createTextRange();
            c.collapse(true);
            c.moveStart("character", d);
            c.moveEnd("character", a - d);
            c.select()
        } else if (this.setSelectionRange) {
            this.focus();
            this.setSelectionRange(d, a)
        }
    }

    function s(d) {
        var a = this.value.length;
        d = d.toLowerCase() == "start" ? "Start" : "End";
        if (document.selection) {
            a = document.selection.createRange();
            var c;
            c = a.duplicate();
            c.expand("textedit");
            c.setEndPoint("EndToEnd", a);
            c = c.text.length - a.text.length;
            a = c + a.text.length;
            return d ==
                "Start" ? c : a
        } else if (typeof this["selection" + d] != "undefined") a = this["selection" + d];
        return a
    }
    var q = {
        codes: {
            188: 44,
            109: 45,
            190: 46,
            191: 47,
            192: 96,
            220: 92,
            222: 39,
            221: 93,
            219: 91,
            173: 45,
            187: 61,
            186: 59,
            189: 45,
            110: 46
        },
        shifts: {
            96: "~",
            49: "!",
            50: "@",
            51: "#",
            52: "$",
            53: "%",
            54: "^",
            55: "&",
            56: "*",
            57: "(",
            48: ")",
            45: "_",
            61: "+",
            91: "{",
            93: "}",
            92: "|",
            59: ":",
            39: '"',
            44: "<",
            46: ">",
            47: "?"
        }
    };
    h.fn.number = function(d, a, c, l) {
        l = typeof l === "undefined" ? "," : l;
        c = typeof c === "undefined" ? "." : c;
        a = typeof a === "undefined" ? 0 : a;
        var i = "\\u" + ("0000" +
                c.charCodeAt(0).toString(16)).slice(-4),
            n = RegExp("[^" + i + "0-9]", "g"),
            o = RegExp(i, "g");
        if (d === true) return this.is("input:text") ? this.on({
            "keydown.format": function(b) {
                var f = h(this),
                    e = f.data("numFormat"),
                    g = b.keyCode ? b.keyCode : b.which,
                    m = "",
                    j = s.apply(this, ["start"]),
                    p = s.apply(this, ["end"]),
                    k = "";
                k = false;
                if (q.codes.hasOwnProperty(g)) g = q.codes[g];
                if (!b.shiftKey && g >= 65 && g <= 90) g += 32;
                else if (!b.shiftKey && g >= 69 && g <= 105) g -= 48;
                else if (b.shiftKey && q.shifts.hasOwnProperty(g)) m = q.shifts[g];
                if (m == "") m = String.fromCharCode(g);
                if (g !== 8 && m != c && !m.match(/[0-9]/)) {
                    f = b.keyCode ? b.keyCode : b.which;
                    if (f == 46 || f == 8 || f == 9 || f == 27 || f == 13 || (f == 65 || f == 82) && (b.ctrlKey || b.metaKey) === true || f >= 35 && f <= 39) return;
                    b.preventDefault();
                    return false
                }
                if ((j == 0 && p == this.value.length || f.val() == 0) && !b.metaKey && !b.ctrlKey && !b.altKey && m.length === 1 && m != 0) {
                    j = p = 1;
                    this.value = "";
                    e.init = a > 0 ? -1 : 0;
                    e.c = a > 0 ? -(a + 1) : 0;
                    r.apply(this, [0, 0])
                } else e.c = p - this.value.length;
                if (a > 0 && m == c && j == this.value.length - a - 1) {
                    e.c++;
                    e.init = Math.max(0, e.init);
                    b.preventDefault();
                    k = this.value.length +
                        e.c
                } else if (m == c) {
                    e.init = Math.max(0, e.init);
                    b.preventDefault()
                } else if (a > 0 && g == 8 && j == this.value.length - a) {
                    b.preventDefault();
                    e.c--;
                    k = this.value.length + e.c
                } else if (a > 0 && g == 8 && j > this.value.length - a) {
                    if (this.value === "") return;
                    if (this.value.slice(j - 1, j) != "0") {
                        k = this.value.slice(0, j - 1) + "0" + this.value.slice(j);
                        f.val(k.replace(n, "").replace(o, c))
                    }
                    b.preventDefault();
                    e.c--;
                    k = this.value.length + e.c
                } else if (g == 8 && this.value.slice(j - 1, j) == l) {
                    b.preventDefault();
                    e.c--;
                    k = this.value.length + e.c
                } else if (a > 0 && j == p &&
                    this.value.length > a + 1 && j > this.value.length - a - 1 && isFinite(+m) && !b.metaKey && !b.ctrlKey && !b.altKey && m.length === 1) {
                    this.value = k = p === this.value.length ? this.value.slice(0, j - 1) : this.value.slice(0, j) + this.value.slice(j + 1);
                    k = j
                }
                k !== false && r.apply(this, [k, k]);
                f.data("numFormat", e)
            },
            "keyup.format": function(b) {
                var f = h(this),
                    e = f.data("numFormat");
                b = b.keyCode ? b.keyCode : b.which;
                var g = s.apply(this, ["start"]);
                if (!(this.value === "" || (b < 48 || b > 57) && (b < 96 || b > 105) && b !== 8)) {
                    f.val(f.val());
                    if (a > 0)
                        if (e.init < 1) {
                            g = this.value.length -
                                a - (e.init < 0 ? 1 : 0);
                            e.c = g - this.value.length;
                            e.init = 1;
                            f.data("numFormat", e)
                        } else if (g > this.value.length - a && b != 8) {
                        e.c++;
                        f.data("numFormat", e)
                    }
                    f = this.value.length + e.c;
                    r.apply(this, [f, f])
                }
            },
            "paste.format": function(b) {
                var f = h(this),
                    e = b.originalEvent,
                    g = null;
                if (window.clipboardData && window.clipboardData.getData) g = window.clipboardData.getData("Text");
                else if (e.clipboardData && e.clipboardData.getData) g = e.clipboardData.getData("text/plain");
                f.val(g);
                b.preventDefault();
                return false
            }
        }).each(function() {
            var b = h(this).data("numFormat", {
                c: -(a + 1),
                decimals: a,
                thousands_sep: l,
                dec_point: c,
                regex_dec_num: n,
                regex_dec: o,
                init: false
            });
            this.value !== "" && b.val(b.val())
        }) : this.each(function() {
            var b = h(this),
                f = +b.text().replace(n, "").replace(o, ".");
            b.number(!isFinite(f) ? 0 : +f, a, c, l)
        });
        return this.text(h.number.apply(window, arguments))
    };
    var t = null,
        u = null;
    if (h.valHooks.text) {
        t = h.valHooks.text.get;
        u = h.valHooks.text.set
    } else h.valHooks.text = {};
    h.valHooks.text.get = function(d) {
        var a = h(d).data("numFormat");
        if (a) {
            if (d.value === "") return "";
            d = +d.value.replace(a.regex_dec_num,
                "").replace(a.regex_dec, ".");
            return "" + (isFinite(d) ? d : 0)
        } else if (h.isFunction(t)) return t(d)
    };
    h.valHooks.text.set = function(d, a) {
        var c = h(d).data("numFormat");
        if (c) return d.value = h.number(a, c.decimals, c.dec_point, c.thousands_sep);
        else if (h.isFunction(u)) return u(d, a)
    };
    h.number = function(d, a, c, l) {
        l = typeof l === "undefined" ? "," : l;
        c = typeof c === "undefined" ? "." : c;
        a = !isFinite(+a) ? 0 : Math.abs(a);
        var i = "\\u" + ("0000" + c.charCodeAt(0).toString(16)).slice(-4);
        d = (d + "").replace(RegExp(i, "g"), ".").replace(RegExp("[^0-9+-Ee.]",
            "g"), "");
        d = !isFinite(+d) ? 0 : +d;
        i = "";
        i = function(n, o) {
            var b = Math.pow(10, o);
            return "" + Math.round(n * b) / b
        };
        i = (a ? i(d, a) : "" + Math.round(d)).split(".");
        if (i[0].length > 3) i[0] = i[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, l);
        if ((i[1] || "").length < a) {
            i[1] = i[1] || "";
            i[1] += Array(a - i[1].length + 1).join("0")
        }
        return i.join(c)
    }
})(jQuery);
/* UItoTop jQuery Plugin 1.2 | Matt Varone | 
http://www.mattvarone.com/web-design/uitotop-jquery-plugin */
(function($) {
    $.fn.UItoTop = function(options) {
        var defaults = {
                text: 'To Top',
                min: 200,
                inDelay: 600,
                outDelay: 400,
                containerID: 'toTop',
                containerHoverID: 'toTopHover',
                scrollSpeed: 1200,
                easingType: 'linear'
            },
            settings = $.extend(defaults, options),
            containerIDhash = '#' + settings.containerID,
            containerHoverIDHash = '#' + settings.containerHoverID;
        $('body').append('<a href="#" id="' + settings.containerID + '">' + settings.text + '</a>');
        $(containerIDhash).hide().on('click.UItoTop', function() {
            $('html, body').animate({
                scrollTop: 0
            }, settings.scrollSpeed, settings.easingType);
            $('#' + settings.containerHoverID, this).stop().animate({
                'opacity': 0
            }, settings.inDelay, settings.easingType);
            return false;
        }).prepend('<span id="' + settings.containerHoverID + '"></span>').hover(function() {
            $(containerHoverIDHash, this).stop().animate({
                'opacity': 1
            }, 600, 'linear');
        }, function() {
            $(containerHoverIDHash, this).stop().animate({
                'opacity': 0
            }, 700, 'linear');
        });
        $(window).scroll(function() {
            var sd = $(window).scrollTop();
            if (typeof document.body.style.maxHeight === "undefined") {
                $(containerIDhash).css({
                    'position': 'absolute',
                    'top': sd + $(window).height() - 50
                });
            }
            if (sd > settings.min)
                $(containerIDhash).fadeIn(settings.inDelay);
            else
                $(containerIDhash).fadeOut(settings.Outdelay);
        });
    };
})(jQuery);