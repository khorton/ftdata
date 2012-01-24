#include <gtk/gtk.h>

/* Define the print_hello function called by menus */
/* to be replaced with a real function eventually*/
static void print_hello( GtkWidget *w,
                         gpointer   data )
{
  g_message ("Hello, World!\n");
}

/* For the radio buttons */
/* to be replaced with a real function eventually*/
/* static void print_selected( gpointer   callback_data, */
/*                             guint      callback_action, */
/*                             GtkWidget *menu_item ) */
/* { */
/*    if(GTK_CHECK_MENU_ITEM(menu_item)->active) */
/*      g_message ("Radio button %d selected\n", callback_action); */
/* } */


/* Our menu, an array of GtkItemFactoryEntry structures that defines each menu item */
static GtkItemFactoryEntry menu_items[] = {
  { "/_File",         NULL,         NULL,           0, "<Branch>" },
  { "/File/_New",     "<control>N", print_hello,    0, "<StockItem>", GTK_STOCK_NEW },
  { "/File/_Open",    "<control>O", print_hello,    0, "<StockItem>", GTK_STOCK_OPEN },
  { "/File/sep1",     NULL,         NULL,           0, "<Separator>" },
  { "/File/_Quit",    "<CTRL>Q", gtk_main_quit, 0, "<StockItem>", GTK_STOCK_QUIT },
/*   { "/_Options",      NULL,         NULL,           0, "<Branch>" }, */
/*   { "/Options/tear",  NULL,         NULL,           0, "<Tearoff>" }, */
/*   { "/Options/Check", NULL,         NULL,   1, "<CheckItem>" }, */
/*   { "/Options/sep",   NULL,         NULL,           0, "<Separator>" }, */
/*   { "/Options/Rad1",  NULL,         print_selected, 1, "<RadioItem>" }, */
/*   { "/Options/Rad2",  NULL,         print_selected, 2, "/Options/Rad1" }, */
/*   { "/Options/Rad3",  NULL,         print_selected, 3, "/Options/Rad1" }, */
  { "/_Help",         NULL,         NULL,           0, "<LastBranch>" },
  { "/_Help/About",   NULL,         NULL,           0, "<Item>" },
};

static gint nmenu_items = sizeof (menu_items) / sizeof (menu_items[0]);

/* Returns a menubar widget made from the above menu */
static GtkWidget *get_menubar_menu( GtkWidget  *window )
{
  GtkItemFactory *item_factory;
  GtkAccelGroup *accel_group;

  /* Make an accelerator group (shortcut keys) */
  accel_group = gtk_accel_group_new ();

  /* Make an ItemFactory (that makes a menubar) */
  item_factory = gtk_item_factory_new (GTK_TYPE_MENU_BAR, "<main>",
                                       accel_group);

  /* This function generates the menu items. Pass the item factory,
     the number of items in the array, the array itself, and any
     callback data for the the menu items. */
  gtk_item_factory_create_items (item_factory, nmenu_items, menu_items, NULL);

  /* Attach the new accelerator group to the window. */
  gtk_window_add_accel_group (GTK_WINDOW (window), accel_group);

  /* Finally, return the actual menu bar created by the item factory. */
  return gtk_item_factory_get_widget (item_factory, "<main>");
}

/* Program Start */
int main( int argc,
          char *argv[] )
{
  GtkWidget *window;
  GtkWidget *main_vbox;
  GtkWidget *menubar;
  GtkWidget *main_hbox;
  GtkWidget *controls_box;
  GtkWidget *mode_selection_box, *entry, *mode_freeze_start, *mode_freeze_end, *mode_slide_time;
  
  
  
 
  /* Initialize GTK */
  gtk_init (&argc, &argv);
 
  /* Make a window */
  window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
  g_signal_connect (G_OBJECT (window), "destroy",
                    G_CALLBACK (gtk_main_quit),
                    NULL);
  gtk_window_set_title (GTK_WINDOW(window), "Flight Test Data");
  gtk_widget_set_size_request (GTK_WIDGET(window), 800, 600);
 
  /* Make a vbox to put the menu, main window, plus bottom controls in */
  main_vbox = gtk_vbox_new (FALSE, 1);
  gtk_container_set_border_width (GTK_CONTAINER (main_vbox), 1);
  gtk_container_add (GTK_CONTAINER (window), main_vbox);
  
  /* Get the menu bar */
  menubar = get_menubar_menu (window);
  
  /* Window to hold box with GTKDataBoxes, plus right scale control */
  main_hbox = gtk_hbox_new (FALSE, 1);

  /* Window to hold bottom controls */
  controls_box = gtk_hbox_new (FALSE, 1);

/* ========================================================================== */
  /* Radio type controls for mode of operation */
  mode_selection_box = gtk_vbox_new (TRUE, 1);
  mode_freeze_start = gtk_radio_button_new_with_label (NULL, "Freeze Start Time");
  entry = gtk_entry_new ();
/* The following line was commented out, as it seemed to produce an Xterm warning. */
/*   gtk_container_add (GTK_CONTAINER (radio1), entry); */
      
  /* Create a radio button with a label */
  mode_freeze_end = gtk_radio_button_new_with_label_from_widget (GTK_RADIO_BUTTON (mode_freeze_start),
							"Freeze End Time");
  /* Create a radio button with a label */
  mode_slide_time = gtk_radio_button_new_with_label_from_widget (GTK_RADIO_BUTTON (mode_freeze_start),
							"Move Time Slice");
  /* Set default radio button */
  gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (mode_slide_time),TRUE);

   /* Pack them into a box, then show all the widgets */
   gtk_box_pack_start (GTK_BOX (mode_selection_box), mode_freeze_start, TRUE, TRUE, 2);
   gtk_box_pack_start (GTK_BOX (mode_selection_box), mode_freeze_end, TRUE, TRUE, 2);
   gtk_box_pack_start (GTK_BOX (mode_selection_box), mode_slide_time, TRUE, TRUE, 2);
   gtk_container_add (GTK_CONTAINER (controls_box), mode_selection_box);

/* ========================================================================== */

  /* Pack it all together */
  gtk_box_pack_start (GTK_BOX (main_vbox), menubar, FALSE, TRUE, 0);
  gtk_box_pack_start (GTK_BOX (main_vbox), main_hbox, FALSE, TRUE, 0);
  gtk_box_pack_end (GTK_BOX (main_vbox), controls_box, FALSE, TRUE, 0);

  /* Show the widgets */
  gtk_widget_show_all (window);
  

/* Test state of mode selection radio buttons */
void toggle_button_callback (GtkWidget *mode_freeze_start, gpointer data)
{
    if (gtk_toggle_button_get_active (GTK_TOGGLE_BUTTON (mode_freeze_start))) {
      g_message ("Mode is Freeze Start!\n");
    } else {
      if (gtk_toggle_button_get_active (GTK_TOGGLE_BUTTON (mode_freeze_end))) {
        g_message ("Mode is Freeze End!\n");
      } else {
        g_message ("Mode is Slide Time!\n");
      }
   }
}
  
  /* Finished! */
  gtk_main ();
 
  return 0;

}