// Basic parametric mounting plate.
// Units are millimeters.

$fn = 64;

plate_length = 80;
plate_width = 36;
plate_thickness = 4;

hole_diameter = 5;
hole_spacing = 54;

module mounting_plate() {
    difference() {
        cube([plate_length, plate_width, plate_thickness], center = true);

        for (x = [-hole_spacing / 2, hole_spacing / 2]) {
            translate([x, 0, 0])
                cylinder(
                    h = plate_thickness + 1,
                    d = hole_diameter,
                    center = true
                );
        }
    }
}

mounting_plate();

