import MenuIcon from "./icons/MenuIcon";
import type { HeaderProps } from "./interfaces";

export default function Header({ toggleSidebar }: HeaderProps) {
  return (
    <>
      <p className="bg-[#e32c1c] border-b border-b-gray-300 flex flex-row-reverse justify-between items-center">
        <button className="border border-white rounded-sm px-2 m-2 text-white">
          Log in
        </button>
        <div className="p-3" onClick={toggleSidebar}>
          <MenuIcon></MenuIcon>
        </div>
      </p>
    </>
  );
}
