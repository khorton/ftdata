/* Test plotting data from a file using GTKDataBox 
 * 
 */
#include <stdio.h>

#include <gtk/gtk.h>
#include <gtkdatabox.h>
#include <math.h>
/* Some versions of math.h have a PI problem... */
#ifndef PI
#define PI 3.14159265358979323846
#endif

#define POINTS 2000


/*----------------------------------------------------------------
 *  databox lissajous
 *----------------------------------------------------------------*/

static gfloat *lissajousX = NULL;
static gfloat *lissajousY = NULL;

static gint lissajous_idle = 0;
static gfloat lissajous_frequency = 3. * PI / 2.;
static GtkWidget *lissajous_label = NULL;
static guint lissajous_counter = 0;

static gboolean
lissajous_idle_func (GtkDatabox * box)
{
   gfloat freq;
   gfloat off;
   gchar label[10];
   gint i;

   if (!GTK_IS_DATABOX (box))
      return FALSE;

   lissajous_frequency += 0.001;
   off = lissajous_counter * 4 * PI / POINTS;

   freq = 14 + 10 * sin (lissajous_frequency);
   for (i = 0; i < POINTS; i++)
   {
      lissajousX[i] = 100. * sin (i * 4 * PI / POINTS + off);
      lissajousY[i] = 100. * cos (i * freq * PI / POINTS + off);
   }


   gtk_databox_redraw (GTK_DATABOX (box));

   sprintf (label, "%d", lissajous_counter++);
   gtk_entry_set_text (GTK_ENTRY (lissajous_label), label);

   return TRUE;
}

static void
create_lissajous (void)
{
   GtkWidget *window = NULL;
   GtkWidget *box1;
   GtkWidget *box2;
   GtkWidget *close_button;
   GtkWidget *box;
   GtkWidget *label;
   GtkWidget *separator;
   GdkColor color;
   gint i;

   lissajous_frequency = 0;
   window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
   gtk_widget_set_size_request (window, 300, 300);

   g_signal_connect (GTK_OBJECT (window), "destroy",
		     GTK_SIGNAL_FUNC (gtk_main_quit), NULL);

   gtk_window_set_title (GTK_WINDOW (window), "Databox: Lissajous Example");
   gtk_container_set_border_width (GTK_CONTAINER (window), 0);

   box1 = gtk_vbox_new (FALSE, 0);
   gtk_container_add (GTK_CONTAINER (window), box1);

   label =
      gtk_label_new
      ("This example resembles an oszilloscope\nreceiving two signals, one is a sine (horizontal),\nthe other is a cosine with ever changing frequency (vertical).\nThe counter is synchron with the updates.");
   gtk_box_pack_start (GTK_BOX (box1), label, FALSE, FALSE, 0);
   separator = gtk_hseparator_new ();
   gtk_box_pack_start (GTK_BOX (box1), separator, FALSE, FALSE, 0);
   lissajous_label = gtk_entry_new ();
   gtk_entry_set_text (GTK_ENTRY (lissajous_label), "0");
   gtk_box_pack_start (GTK_BOX (box1), lissajous_label, FALSE, FALSE, 0);
   separator = gtk_hseparator_new ();
   gtk_box_pack_start (GTK_BOX (box1), separator, FALSE, FALSE, 0);

   lissajous_idle = 0;
   lissajous_frequency = 3. * PI / 2.;
   lissajous_counter = 0;

   box = gtk_databox_new ();

   lissajousX = g_new0 (gfloat, POINTS);
   lissajousY = g_new0 (gfloat, POINTS);

   for (i = 0; i < POINTS; i++)
   {
      lissajousX[i] = 100. * sin (i * 4 * PI / POINTS);
      lissajousY[i] = 100. * cos (i * 4 * PI / POINTS);
   }
   color.red = 65535;
   color.green = 65535;
   color.blue = 0;

   gtk_databox_data_add (GTK_DATABOX (box), POINTS,
			 lissajousX, lissajousY, color,
			 GTK_DATABOX_LINES, 0);

   color.red = 0;
   color.green = 0;
   color.blue = 32768;
   gtk_databox_set_background_color (GTK_DATABOX (box), color);

   gtk_databox_rescale (GTK_DATABOX (box));

   gtk_box_pack_start (GTK_BOX (box1), box, TRUE, TRUE, 0);

   separator = gtk_hseparator_new ();
   gtk_box_pack_start (GTK_BOX (box1), separator, FALSE, TRUE, 0);

   box2 = gtk_vbox_new (FALSE, 10);
   gtk_container_set_border_width (GTK_CONTAINER (box2), 10);
   gtk_box_pack_end (GTK_BOX (box1), box2, FALSE, TRUE, 0);
   close_button = gtk_button_new_with_label ("close");

   g_signal_connect_swapped (GTK_OBJECT (close_button), "clicked",
			     GTK_SIGNAL_FUNC (gtk_main_quit),
			     GTK_OBJECT (box));

   gtk_box_pack_start (GTK_BOX (box2), close_button, TRUE, TRUE, 0);
   GTK_WIDGET_SET_FLAGS (close_button, GTK_CAN_DEFAULT);
   gtk_widget_grab_default (close_button);
   lissajous_idle = gtk_idle_add ((GtkFunction) lissajous_idle_func, box);

   gtk_widget_show_all (window);
}

void
read_data ()
{
   char *line[2000];
   /* open file */
   FILE *data_file;
   data_file=fopen("/Users/kwh/ftdata.old/Tk/0510251651.csv", "r");
   fgets(*line, 2000, data_file);
   puts(*line);
   fclose(data_file);
}

gint
main (gint argc, char *argv[])
{
   gtk_init (&argc, &argv);

   read_data ();
   create_lissajous ();
   gtk_main ();

   return 0;
}
