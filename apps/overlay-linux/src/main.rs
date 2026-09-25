use gtk4 as gtk;
use gtk::prelude::*;
use gtk4_layer_shell::{Edge, KeyboardMode, Layer, LayerShell};
use signal_hook::consts::SIGINT;
use signal_hook::iterator::Signals;
use std::thread;

fn main() {
    // GTK normally terminates on SIGINT, but the explicit handler makes the
    // development spike deterministic and gives us a clean shutdown path for
    // the eventual renderer/native overlay process.
    let mut signals = Signals::new([SIGINT]).expect("failed to install SIGINT handler");
    thread::spawn(move || {
        if signals.forever().next().is_some() {
            eprintln!("Fruit-Fly: received Ctrl+C (SIGINT), shutting down.");
            std::process::exit(0);
        }
    });

    let app = gtk::Application::builder()
        .application_id("dev.fruitfly.Overlay")
        .build();

    app.connect_activate(build_ui);
    app.run();
}

fn build_ui(app: &gtk::Application) {
    let window = gtk::ApplicationWindow::builder()
        .application(app)
        .title("Fruit-Fly Overlay Spike")
        .decorated(false)
        .build();

    window.init_layer_shell();
    window.set_layer(Layer::Overlay);
    window.set_keyboard_mode(KeyboardMode::None);
    window.set_exclusive_zone(-1);

    for edge in [Edge::Top, Edge::Bottom, Edge::Left, Edge::Right] {
        window.set_anchor(edge, true);
    }

    let canvas = gtk::DrawingArea::new();
    canvas.set_content_width(1000);
    canvas.set_content_height(700);
    canvas.set_draw_func(|_, cr, width, height| {
        let x = width as f64 * 0.82;
        let y = height as f64 * 0.72;

        cr.set_source_rgba(0.42, 0.03, 0.14, 0.88);
        cr.arc(x, y, 52.0, 0.0, std::f64::consts::TAU);
        let _ = cr.fill();

        cr.set_source_rgba(1.0, 0.9, 0.9, 0.9);
        for ex in [x - 17.0, x + 17.0] {
            cr.arc(ex, y - 8.0, 5.5, 0.0, std::f64::consts::TAU);
            let _ = cr.fill();
        }
    });

    window.set_child(Some(&canvas));
    window.present();
}
